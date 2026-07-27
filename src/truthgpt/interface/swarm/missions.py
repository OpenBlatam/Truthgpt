"""
Swarm Missions — Continuous and background mission execution.

Extracted from swarm_menu.py for maintainability.
"""

import asyncio
import time
import inspect
import logging
from collections import deque
from pathlib import Path
from typing import List, Optional

from rich.panel import Panel
from rich.table import Table
from rich.prompt import FloatPrompt, Prompt

from truthgpt.interface.core import (
    console, USER_PREFS, log_activity, clear_screen,
    get_header, wait_for_user, get_input,
    background_missions, save_mission_output, extract_target_directory,
)
from truthgpt.interface.cc_style import (
    cc_action, cc_tool_call, cc_result, cc_agent_done, cc_spinner, _fmt_tokens,
)

logger = logging.getLogger(__name__)


# Shared directive injected into every autonomous-mission prompt so agents act
# without waiting for input. Kept as one constant so the generation and
# refinement prompts can never drift apart.
_AUTONOMOUS_DIRECTIVE = (
    "CRITICAL INSTRUCTION: You are running in a fully autonomous background mission. "
    "DO NOT ask the user for clarification or wait for input. "
    "Make your best assumptions, execute the necessary actions, and provide a definitive 'final_answer'."
)

# A reward strictly below this triggers a self-correction (refine) pass.
_REFINE_THRESHOLD = 0.75

# Hard ceiling on any single LLM call in an autonomous loop. Without this a
# hung/unreachable provider freezes the whole mission at "0 tokens" forever
# (no streamed response ever arrives). On timeout the call is abandoned and the
# loop's existing retry/fallback path takes over instead of blocking.
_LLM_CALL_TIMEOUT = 180.0


async def _call_with_timeout(awaitable, timeout: float = _LLM_CALL_TIMEOUT):
    """Await *awaitable* but raise ``asyncio.TimeoutError`` after *timeout* sec.

    Keeps a stalled provider from freezing an autonomous mission. Callers wrap
    this in their normal try/except so a timeout is treated like any other
    generation error (retry, fall back, or skip).
    """
    return await asyncio.wait_for(awaitable, timeout=timeout)


def _parse_reward(text: str, default: float = 0.5) -> float:
    """Extract a 0.0–1.0 reward score from a free-form LLM judgment.

    Scans for the first in-range number, tolerating formats like ``0.85``,
    ``.9``, ``1``, or ``Score: 0.7``. Returns *default* when nothing parseable
    is found and clamps out-of-range values into [0, 1].
    """
    import re
    for tok in re.findall(r"\d*\.\d+|\d+", str(text)):
        try:
            val = float(tok)
        except ValueError:
            continue
        if 0.0 <= val <= 1.0:
            return val
    return default


def _reward_bar(score: float, width: int = 12) -> str:
    """Render a Claude-Code-style inline progress bar for a reward score."""
    filled = max(0, min(width, round(score * width)))
    color = "green" if score >= 0.75 else "yellow" if score >= 0.5 else "red"
    bar = "█" * filled + "░" * (width - filled)
    return f"[{color}]{bar}[/{color}] {score:.2f}/1.0"


def _repair_json(text: str) -> str:
    """Escape raw control chars that appear *inside* JSON string literals.

    LLMs frequently emit JSON with literal newlines/tabs inside string values,
    which is technically invalid and makes ``json.loads`` fail. This walks the
    text and escapes those control chars only when inside a string.
    """
    out = []
    in_str = False
    esc = False
    for ch in text:
        if esc:
            out.append(ch)
            esc = False
            continue
        if ch == "\\":
            out.append(ch)
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            out.append(ch)
            continue
        if in_str and ch in "\n\r":
            out.append("\\n")
            continue
        if in_str and ch == "\t":
            out.append("\\t")
            continue
        out.append(ch)
    return "".join(out)


def _coerce_agent_payload(content: str):
    """Best-effort parse of a structured agent payload from *content*.

    Returns a dict with optional 'thought'/'final_answer'/'metadata' keys, or
    ``None`` if *content* is plain text (no structured envelope detected).
    """
    import json
    import re

    text = content.strip()
    if not (text.startswith("{") and '"' in text):
        # Maybe wrapped in a ```json fence
        m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
        if not m:
            return None
        text = m.group(1)

    data = None
    for candidate in (text, _repair_json(text)):
        try:
            data = json.loads(candidate)
            break
        except Exception:
            continue
    if not isinstance(data, dict):
        return None
    if not any(k in data for k in ("thought", "final_answer", "answer", "metadata")):
        return None
    return data


def _provider_for_model(model_id: str) -> str:
    """Map a concrete model id back to the provider/engine that owns it.

    Lets the UI always name *which* engine produced an output — Claude,
    OpenRouter, DeepSeek, etc. — even on the cost cascade or in an ensemble
    where several providers are in play.
    """
    m = (model_id or "").lower()
    if not m:
        return "engine"
    if "/" in m or m.startswith("~"):
        return "openrouter"
    if "deepseek" in m:
        return "deepseek"
    if m.startswith(("gpt", "o1", "o3", "o4")) or "openai" in m:
        return "openai"
    if "gemini" in m or "google" in m:
        return "google"
    if "claude" in m or "anthropic" in m:
        return "claude"
    return "engine"


def _attribution(llm, content: str = "") -> str:
    """Human ``provider · model`` label for whichever model produced *content*.

    Resolves attribution across all three engine paths so every output can say
    who did it:
      • ensemble → the winning engine recorded in the payload metadata,
      • cascade  → the model the FrugalGPT ladder actually resolved with,
      • single   → the one configured provider/model.
    Returns "" when nothing can be determined.
    """
    # 1. Ensemble: the merged payload records the winning engine + its model.
    data = _coerce_agent_payload(content) if content else None
    meta = data.get("metadata") if isinstance(data, dict) and isinstance(data.get("metadata"), dict) else None
    if meta:
        winner = meta.get("winner")
        model = meta.get("winner_model")
        if winner and model:
            return f"{winner} · {model}"
        if model:
            return f"{_provider_for_model(model)} · {model}"
        if winner:
            return str(winner)

    # 2. Cost cascade: stats track the model that resolved the last call.
    stats = getattr(llm, "cascade_stats", None)
    if isinstance(stats, dict) and stats.get("last"):
        used = stats["last"]
        if used == "cache":
            return "caché (sin nueva llamada al modelo)"
        return f"{_provider_for_model(used)} · {used}"

    # 3. Single engine (or ensemble with no recorded winner).
    provider = getattr(llm, "provider_name", None)
    model = getattr(llm, "model_name", None)
    if provider and model:
        return f"{provider} · {model}"
    return model or provider or ""


def _render_thinking(thought: str, max_lines: int = 18) -> None:
    """Show the agent reasoning as a dim, collapsible Claude-style block."""
    from truthgpt.interface.cc_style import SPIN_FRAMES
    glyph = SPIN_FRAMES[2] if SPIN_FRAMES else "*"
    console.print(f"[magenta]{glyph}[/magenta] [dim]Thinking[/dim]")
    lines = [l.strip() for l in thought.splitlines() if l.strip()]
    for line in lines[:max_lines]:
        console.print(f"  [dim italic]{line}[/dim italic]")
    remaining = len(lines) - max_lines
    if remaining > 0:
        console.print(f"  [dim italic]… +{remaining} more line{'s' if remaining != 1 else ''}[/dim italic]")


def _render_answer_body(answer: str, title: str) -> None:
    """Render the final answer, syntax-highlighting any fenced code blocks."""
    import re
    from rich.syntax import Syntax

    parts = re.split(r"```([a-zA-Z0-9+#_-]*)\n(.*?)\n```", answer, flags=re.DOTALL)
    # re.split with 2 groups yields: [prose, lang, code, prose, lang, code, ...]
    if len(parts) == 1:
        console.print(Panel(answer or "[dim](empty)[/dim]", title=title, border_style="green"))
        return

    console.print(f"[green]{('●')}[/green] [bold]{title}[/bold]")
    i = 0
    while i < len(parts):
        prose = parts[i].strip()
        if prose:
            console.print(Panel(prose, border_style="green", expand=False))
        if i + 2 < len(parts):
            lang = (parts[i + 1] or "text").strip() or "text"
            code = parts[i + 2]
            try:
                console.print(Syntax(code, lang, theme="ansi_dark", line_numbers=True, word_wrap=True))
            except Exception:
                console.print(Panel(code, border_style="cyan"))
        i += 3


def _render_change(prev: str, curr: str, title: str) -> None:
    """Render a Claude-Code-style +added / −removed diff between two outputs."""
    import difflib
    from rich.text import Text

    diff = list(difflib.unified_diff(
        prev.splitlines(), curr.splitlines(), lineterm="",
    ))
    added = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))

    if added == 0 and removed == 0:
        console.print(f"  [dim]{title}: no changes from previous iteration[/dim]")
        return

    console.print(
        f"[green]●[/green] [bold]{title}[/bold]  "
        f"[green]+{added}[/green] [red]−{removed}[/red]"
    )
    for line in diff:
        if line.startswith(("+++", "---", "@@")):
            continue
        row = Text("  ")
        if line.startswith("+"):
            row.append("+ ", style="green")
            row.append(line[1:], style="green")
        elif line.startswith("-"):
            row.append("− ", style="red")
            row.append(line[1:], style="red")
        else:
            row.append("  ")
            row.append(line[1:] if line.startswith(" ") else line, style="dim")
        console.print(row)


def _render_mission_output(content: str, iteration: int, previous: str = "") -> str:
    """Render the iteration result the way Claude Code surfaces a turn:

    a dim *thinking* block, then — if this refines a prior iteration — a
    +added/−removed diff (else the full answer with syntax-highlighted code),
    and a discreet metadata footer. Returns the answer text for the next diff.
    """
    title = f"🤖 Mission Output (Iter {iteration})"
    data = _coerce_agent_payload(content)
    if data is None:
        body = content.strip()
        thought, answer, meta = "", body, None
    else:
        thought = (data.get("thought") or data.get("reasoning") or "").strip()
        answer = (data.get("final_answer") or data.get("answer") or "").strip()
        meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else None

    if thought:
        _render_thinking(thought)

    if answer:
        if previous and previous.strip() and previous.strip() != answer:
            _render_change(previous, answer, f"Changes (Iter {iteration})")
        else:
            _render_answer_body(answer, title)
    else:
        cc_result("no final_answer yet — agent is still planning / issuing tool calls")

    if meta:
        bits = []
        if meta.get("ensemble_mode"):
            bits.append(f"ensemble: {meta['ensemble_mode']}")
        if meta.get("winner"):
            wm = meta.get("winner_model")
            bits.append(f"winner: {meta['winner']}" + (f" ({wm})" if wm else ""))
        engines = meta.get("engines")
        if engines:
            bits.append("engines: " + ", ".join(map(str, engines)))
        if bits:
            console.print(f"  [dim]{' · '.join(bits)}[/dim]")

    return answer


def _report_cost_savings(llm) -> None:
    """Surface FrugalGPT cascade savings, resolver model and cache hit rate."""
    optimizer = getattr(llm, "cost_optimizer", None)
    if optimizer is None:
        return
    try:
        cache = optimizer.cache.get_stats()
        savings = getattr(optimizer.budget, "savings_usd", 0.0)
        spend = getattr(optimizer.budget.metrics, "total_usd", 0.0)
        bits = [f"💸 spend ${spend:.4f}", f"saved ${savings:.4f}"]

        stats = getattr(llm, "cascade_stats", None)
        if stats and stats.get("calls"):
            last = stats.get("last")
            if last and last != "cache":
                top = getattr(llm, "cascade_models", [None])[-1]
                tag = "top" if last == top else "cheaper"
                bits.append(f"resolved by {last} ({tag})")
            elif last == "cache":
                bits.append("served from cache")
            avoided = stats["resolved_below_top"] + stats["cache_hits"]
            bits.append(f"top-model avoided {avoided}/{stats['calls']}")

        if cache.get("total_requests"):
            bits.append(f"cache {cache.get('hit_rate', 0.0) * 100:.0f}% hits")
        console.print(f"  [dim]{' · '.join(bits)}[/dim]")
    except Exception:
        pass


# ── Platform-aware keyboard interrupt ─────────────────────────────

async def wait_with_interrupt(seconds: float) -> str:
    """Wait for *seconds* with keyboard-driven shortcuts.

    Returns one of: 'continue', 'menu', 'query', 'background', 'export', 'stop'.
    """
    try:
        import msvcrt  # Windows only
    except ImportError:
        # Cross-platform fallback — just sleep
        await asyncio.sleep(seconds)
        return "continue"

    steps = int(seconds)
    if steps <= 0:
        return "continue"

    console.print(
        f"\n[dim]● Waiting {seconds / 60:.1f}m before next iteration  "
        "[bold white]M[/bold white] menu · "
        "[bold white]Q[/bold white] query · "
        "[bold white]B[/bold white] background · "
        "[bold white]X[/bold white] export · "
        "[bold white]S[/bold white] stop[/dim]"
    )
    for _ in range(steps):
        await asyncio.sleep(1)
        if msvcrt.kbhit():
            key = msvcrt.getch().decode("utf-8").upper()
            key_map = {"M": "menu", "Q": "query", "B": "background", "X": "export", "S": "stop"}
            if key in key_map:
                return key_map[key]
    return "continue"


# ── Background Mission ────────────────────────────────────────────

class BackgroundMission:
    def __init__(self, name, query, interval, team, agents_map, config, llm, context):
        self.name = name
        self.query = query
        self.interval = interval
        self.team = team
        self.agents_map = agents_map
        self.config = config
        self.llm = llm
        self.context = context
        self.history: list = []
        self.status = "Running"
        self.last_run: Optional[str] = None
        self.task = None

    async def run_loop(self):
        cycle = 0
        recent_answers: deque = deque(maxlen=3)  # rolling memory of prior cycles
        while self.status == "Running":
            cycle += 1
            self.last_run = time.strftime("%H:%M:%S")
            log_activity("BG Mission", f"Cycle: {self.name}", status="Running")
            cc_action(f'Background mission "{self.name}" · cycle {cycle}', status="RUN")

            # Seed the cycle with a rolling summary of prior cycles so each new
            # cycle ADVANCES the mission instead of restarting from the same
            # query (which made successive cycles repeat the same work).
            if recent_answers:
                history_block = (
                    "Work already completed in prior cycles (most recent last):\n"
                    + "\n".join(f"- [cycle {n}] {a[:300]}" for n, a in recent_answers)
                    + "\n\n"
                )
                current_prompt = (
                    f"Persistent mission: {self.query}\n\n{history_block}"
                    "Continue by ADVANCING the mission; build on the completed work "
                    "above, do not repeat it."
                )
            else:
                current_prompt = self.query
            cycle_history = []
            last_content: Optional[str] = None

            try:
                for key in self.team:
                    if key not in self.agents_map and key != "arxiv_discovery_scout":
                        continue

                    t0 = time.time()
                    if key == "arxiv_discovery_scout":
                        cc_tool_call(f"{key}: discovering & integrating papers…")
                        from truthgpt.agents.domains.system_intelligence.research_agent import ResearchAgent
                        agent = ResearchAgent(llm_engine=self.llm)
                        res = await _call_with_timeout(agent.process(f"discover and integrate papers for {current_prompt}"))
                        content = res.content
                    else:
                        cc_tool_call(f"{key}: running cognitive cycle…")
                        agent_cls = self.agents_map[key]
                        sig = inspect.signature(agent_cls.__init__)
                        params = {}
                        if "config" in sig.parameters:
                            params["config"] = self.config
                        if "llm_engine" in sig.parameters:
                            params["llm_engine"] = self.llm
                        agent = agent_cls(**params)
                        res = await _call_with_timeout(agent.process(current_prompt, context=self.context))
                        content = res.content if hasattr(res, "content") else str(res)

                    cc_agent_done(key, ok=True)
                    cc_result(
                        f"{key}",
                        note=f"{time.time() - t0:.1f}s · ~{_fmt_tokens(len(content) // 4)} tokens",
                    )
                    cycle_history.append({"phase": key, "output": content})
                    last_content = content
                    current_prompt = f"Previous findings: {content}\n\nTask: {current_prompt}"

                self.history.append({"time": self.last_run, "data": cycle_history})
                # Carry this cycle's final output into the next cycle's memory.
                if last_content is not None:
                    recent_answers.append((cycle, last_content.strip()))
                cc_result(f'cycle {cycle} complete · {len(cycle_history)} phase(s)')
            except Exception as e:
                detail = str(e) or type(e).__name__
                log_activity("BG Mission", f"Error in {self.name}: {detail}", status="Error")
                logger.error(f"Background mission {self.name} encountered error: {detail}")
                cc_action(f'Background mission "{self.name}" cycle {cycle} failed: {detail}', status="ERROR")

            await asyncio.sleep(self.interval * 60)


# ── Continuous Mission ────────────────────────────────────────────

def _save_code_blocks_if_needed(content: str, query: str, iteration: int):
    """Extract code blocks and persist them if a target directory is detectable."""
    target_dir = extract_target_directory(query)
    if target_dir:
        from truthgpt.interface.swarm.fusion import save_code_blocks_to_directory
        cc_tool_call(f"Writing code blocks to {target_dir}…")
        save_code_blocks_to_directory(content, target_dir, default_prefix=f"output_iter_{iteration}")


async def handle_continuous_mission():
    clear_screen()
    console.print(get_header())
    console.print(Panel(
        "[bold yellow]🔁 Autonomous RLHF Mission Mode[/bold yellow]\n"
        "[dim]Agent will self-evaluate, assign heuristic rewards, and recursively refine.[/dim]",
        expand=False,
    ))
    query = get_input("Enter the persistent mission query")
    interval_min = FloatPrompt.ask("Execution interval (minutes)", default=1.0)

    console.print(
        "\n[bold]Engine tier[/bold] [dim](applies to the whole configured engine set)[/dim]\n"
        "  [green]1[/green]) Economy  — fast, cheap models (flash / haiku / mini)\n"
        "  [yellow]2[/yellow]) Standard — balanced models (pro / sonnet / 4o)\n"
        "  [red]3[/red]) Premium  — best models (reasoner / opus / pro)"
    )
    tier_choice = Prompt.ask("Tier", choices=["1", "2", "3"], default="2")
    tier = {"1": "economica", "2": "media", "3": "alta"}[tier_choice]
    # English label for display only; the internal key above is what the engine
    # registry's TIER_MODELS / cascade ladders are keyed on, so it stays as-is.
    tier_label = {"economica": "economy", "media": "standard", "alta": "premium"}[tier]

    # Cost optimization: run a FrugalGPT cascade (cheap→tier-top) + semantic cache +
    # prompt compression so the best models are only paid for when really needed.
    console.print(
        "\n[bold]Cost optimization[/bold] [dim](economy→tier cascade, semantic cache, compression)[/dim]\n"
        "[dim]Reduces spend on the best models by escalating only when needed.[/dim]"
    )
    cost_optimized = Prompt.ask(
        "Cost optimization", choices=["y", "n"], default="y"
    ) == "y"

    console.print(
        f"\n[green]✓ Mission started: '{query}'[/green] "
        f"[dim](tier: {tier_label}{', cost-opt' if cost_optimized else ''})[/dim]"
    )

    from truthgpt.agents.framework.interfaces.client.client import AgentClient
    from truthgpt.agents.framework.engines import engine_registry

    # Disable the semantic cache on the cost path: this is a self-refining loop,
    # so near-identical prompts across iterations must NOT replay the first
    # cached answer (the cause of "always the same response"). The cheap→tier
    # cascade still applies, so cost optimization is preserved.
    llm = engine_registry.build_tiered_engine(
        tier, USER_PREFS["preferred_engine"], cost_optimized=cost_optimized,
        enable_cache=False,
    )
    if getattr(llm, "cost_optimizer", None) is not None:
        console.print(f"[dim]🧩 Cascade ({llm.provider_name}): {llm.model_name}[/dim]")
    else:
        console.print(f"[dim]🧩 Engines: {getattr(llm, 'model_name', 'unknown')}[/dim]")
    client = AgentClient(use_swarm=True, llm_engine=llm)

    # Task Decomposition
    cc_action("Decomposing mission into sub-objectives", status="RUN")
    try:
        with cc_spinner("Planning"):
            decomposition_res = await _call_with_timeout(client.swarm.route_and_process(
                f"Decompose this mission into 3 distinct sequential steps: {query}",
                context={"user_id": "rlhf_planner"},
            ))
        plan = decomposition_res.content if hasattr(decomposition_res, "content") else str(decomposition_res)
        for line in (l.strip() for l in plan.splitlines() if l.strip()):
            cc_result(line[:160])
    except Exception as e:
        cc_action(f"Skipping decomposition: {e}", status="WARN")

    try:
        iteration = 1
        recent_answers: deque = deque(maxlen=3)  # rolling memory of prior iterations
        previous_answer = ""
        last_score: Optional[float] = None
        while True:
            console.print()
            cc_action(f"RLHF Iteration {iteration}", status="RUN")

            # Step 1: Generation. Feed back a rolling summary of prior iterations
            # and explicitly ask the agent to ADVANCE the mission rather than
            # restate earlier work — otherwise outputs converge on repetition.
            if recent_answers:
                history_block = (
                    "Work already completed in prior iterations (most recent last):\n"
                    + "\n".join(f"- [iter {n}] {a[:300]}" for n, a in recent_answers)
                    + "\n\n"
                )
            else:
                history_block = ""
            prompt = (
                f"Persistent mission: {query}\n\n"
                f"{history_block}"
                "Produce the NEXT concrete step that ADVANCES the mission. "
                "Build on the completed work above; do not repeat or merely restate it.\n\n"
                f"{_AUTONOMOUS_DIRECTIVE}"
            )
            try:
                t0 = time.time()
                cc_tool_call("Generating next step…")
                with cc_spinner("Generating") as sp:
                    response = await _call_with_timeout(client.swarm.route_and_process(
                        prompt,
                        context={"user_id": "continuous_mission"},
                    ))
                    if getattr(response, "action_type", None) == "error":
                        raise Exception(f"Agent returned error state: {getattr(response, 'content', 'Unknown error')}")
                    content = response.content if hasattr(response, "content") else str(response)
                    sp.add_tokens(len(content) // 4)
                gen_note = f"{time.time() - t0:.1f}s · ~{_fmt_tokens(len(content) // 4)} tokens"
                who = _attribution(llm, content)
                if who:
                    gen_note = f"{who} · {gen_note}"
                cc_result("generation", note=gen_note)
            except asyncio.TimeoutError:
                cc_action(
                    f"Generation timed out after {_LLM_CALL_TIMEOUT:.0f}s — provider unresponsive",
                    status="ERROR",
                )
                cc_tool_call("Retrying in 10 seconds…")
                await asyncio.sleep(10)
                continue
            except Exception as e:
                cc_action(f"Generation error: {e}", status="ERROR")
                cc_tool_call("Retrying in 10 seconds…")
                await asyncio.sleep(10)
                continue


            # Step 2: RLHF Reward Evaluation (Self-Refine). Ground the judgment in
            # the mission so the score reflects progress, not generic polish.
            cc_tool_call("Self-evaluating output quality…")
            judge = ""
            try:
                eval_prompt = (
                    "On a scale from 0.0 to 1.0, rate how well the OUTPUT advances the "
                    "mission in accuracy, depth, and helpfulness. Return ONLY a float "
                    f"like 0.85.\nMission: {query}\nOutput: {content[:1000]}"
                )
                with cc_spinner("Scoring"):
                    eval_res = await _call_with_timeout(llm(eval_prompt))
                reward_score = _parse_reward(str(eval_res))
                judge = _attribution(llm, str(eval_res))
            except Exception:
                reward_score = 0.5

            trend = ""
            if last_score is not None:
                delta = reward_score - last_score
                arrow = "↑" if delta > 0.01 else "↓" if delta < -0.01 else "→"
                trend = f"  [dim]{arrow} {delta:+.2f} vs prev[/dim]"
            cc_result(f"reward {_reward_bar(reward_score)}{trend}", note=f"judge: {judge}" if judge else "")
            last_score = reward_score

            if reward_score < _REFINE_THRESHOLD:
                cc_action("Score below threshold — self-correcting", status="WARN")
                try:
                    refine_prompt = (
                        f"This output scored {reward_score:.2f}/1.0 on the mission "
                        f"'{query}'. Improve it — fix errors, add depth, and make it "
                        f"more useful:\n{content}\n\n"
                        f"{_AUTONOMOUS_DIRECTIVE}"
                    )
                    with cc_spinner("Refining") as sp:
                        refine_res = await _call_with_timeout(client.swarm.route_and_process(
                            refine_prompt,
                            context={"user_id": "continuous_mission"},
                        ))
                    is_error = getattr(refine_res, "action_type", None) == "error"
                    if is_error:
                        cc_result("refinement hit a reasoning limit — keeping original output")
                    else:
                        content = refine_res.content if hasattr(refine_res, "content") else str(refine_res)
                        cc_agent_done("Self-Refine", ok=True)
                except Exception as e:
                    cc_action(f"Refinement failed: {e}", status="ERROR")

            previous_answer = _render_mission_output(content, iteration, previous=previous_answer)

            _report_cost_savings(llm)

            # Record this iteration's final (post-refine) output so the next
            # iteration can build on it instead of repeating it.
            recent_answers.append((iteration, content.strip()))

            _save_code_blocks_if_needed(content, query, iteration)

            action = await wait_with_interrupt(interval_min * 60)
            if action in ("stop", "menu"):
                break
            elif action == "query":
                new_query = get_input("Enter new persistent mission query", default=query)
                if new_query.strip():
                    query = new_query.strip()
                    recent_answers.clear()  # prior history no longer applies
                    last_score = None
                    console.print(f"[green]✓ Mission query updated to: '{query}'[/green]")
            elif action == "export":
                save_mission_output(content, mission_name="Continuous", query=query)

            iteration += 1
    except KeyboardInterrupt:
        console.print("\n[red]Mission terminated by user.[/red]")


# ── Background Mission Dashboard ─────────────────────────────────

async def handle_background_missions():
    clear_screen()
    console.print(get_header())
    console.print("[bold cyan]📡 Active Background Missions[/bold cyan]")
    if not background_missions:
        console.print("[yellow]No missions running in background.[/yellow]")
        wait_for_user(force=True)
        return
    table = Table()
    table.add_column("#")
    table.add_column("Mission Name")
    table.add_column("Interval")
    table.add_column("Last Run")
    table.add_column("Status")
    for i, m in enumerate(background_missions, 1):
        table.add_row(str(i), m.name, f"{m.interval}m", m.last_run or "Pending", m.status)
    console.print(table)
    cmd = get_input("Action")
    if cmd == "0":
        return
