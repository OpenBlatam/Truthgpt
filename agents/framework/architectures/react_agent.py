from __future__ import annotations
import logging
import re
import asyncio
import json
import uuid
from typing import List, Dict, Any, Callable, Protocol, Optional, runtime_checkable, Type, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from optimization_core.agents.framework.memory.sqlite_memory import SQLiteMemory, BaseMemory
    from optimization_core.agents.framework.memory.vector_memory import VectorMemory
    from optimization_core.agents.framework.memory.core_memory import CoreMemory
    from optimization_core.agents.framework.tools.tools import BaseTool, ToolResult
    from optimization_core.agents.framework.engines.engines import AsyncLLMEngine
    from typing import AsyncIterator

from optimization_core.agents.framework.models import AgentAction, AgentResponse, InferenceResult, AgentConfig
from optimization_core.agents.framework.tools.config import settings

try:
    from interface.cc_style import (
        cc_action, cc_tool_call, cc_result, cc_agent_done, cc_code_change, cc_tool_output
    )
    CC_AVAILABLE = True
except ImportError:
    CC_AVAILABLE = False

from optimization_core.agents.framework.utils import parse_agent_action

try:
    from optimization_core.agents.framework.observability import global_tracer
except ImportError:
    from optimization_core.agents.framework.observability import global_tracer

logger = logging.getLogger(__name__)

class MultiUserReActAgent:
    """
    Orquestador ReAct Multi-Usuario de Grado Empresarial.
    Gestión asíncrona de bucles de razonamiento e integración Pydantic (JSON).
    """

    def __init__(
        self, 
        config: AgentConfig,
        llm_engine: Optional[AsyncLLMEngine] = None, 
        memory: Optional[BaseMemory] = None,
        vector_memory: Optional[VectorMemory] = None,
        custom_system_instructions: Optional[str] = None,
        tools: Optional[List[BaseTool]] = None,
        scheduler: Optional[Any] = None
    ):
        from optimization_core.agents.framework.memory.sqlite_memory import SQLiteMemory
        from optimization_core.agents.framework.memory.core_memory import CoreMemory
        from optimization_core.agents.framework.memory.core_memory_tools import CoreMemoryAppendTool, CoreMemoryReplaceTool

        self.config = config
        self.llm = llm_engine or config.llm_engine
        self.memory = memory or SQLiteMemory(db_path=config.memory_db_path)
        self.vector_memory = vector_memory
        self.core_memory = CoreMemory()
        self.tools: Dict[str, BaseTool] = {}
        self.custom_system_instructions = custom_system_instructions
        self.use_reflexion = config.use_reflexion
        self.name = "MultiUserReActAgent"
        self.persistent = getattr(config, "persistent", True)

        if scheduler:
            self.scheduler = scheduler
        else:
            from optimization_core.agents.orchestration.scheduler.smart_scheduler import SmartAgentScheduler
            self.scheduler = SmartAgentScheduler()

        if tools:
            for tool in tools:
                self.register_tool(tool)
        
        # Add memory self-update tools
        self.register_tool(CoreMemoryAppendTool(self.core_memory))
        self.register_tool(CoreMemoryReplaceTool(self.core_memory))

    def register_tool(self, tool: BaseTool) -> None:
        """Registra una herramienta disponible para el agente."""
        self.tools[tool.name] = tool
        logger.info(f"Agente {self.name}: Herramienta '{tool.name}' registrada.")

    async def load_mcp_tools(self, server_url: str):
        """
        Descubre y registra dinámicamente herramientas desde un servidor MCP.
        """
        from optimization_core.agents.framework.interfaces.client.mcp_client import MCPClient
        from optimization_core.agents.framework.tools.tools import MCPTool

        logger.info(f"Cargando herramientas MCP desde {server_url}...")
        client = MCPClient(server_url)
        tools_info = await client.list_tools()
        
        for t_info in tools_info:
            mcp_tool = MCPTool(client, t_info)
            self.register_tool(mcp_tool)
        
        logger.info(f"Se cargaron {len(tools_info)} herramientas MCP.")

    def _get_system_instructions(self) -> str:
        """Genera instrucciones dinámicas usando el PromptManager centralizado."""
        from optimization_core.agents.framework.prompts.prompt_manager import prompt_manager
        
        tools_list = "\n".join([f"- {t.name}: {t.description}" for t in self.tools.values()])
        
        # Build prompt using centralized templates
        base = prompt_manager.get_prompt("base_agent", name=settings.AGENT_NAME, role="Enterprise AI Assistant")
        react = prompt_manager.get_prompt("react_core")
        json_schema = prompt_manager.get_prompt("json_output", schema=AgentAction.model_json_schema())
        
        instructions = f"{base}\n{react}\n\nTienes acceso a estas herramientas:\n{tools_list}\n\n"
        if self.custom_system_instructions:
            instructions += f"{self.custom_system_instructions}\n\n"
            
        return instructions + json_schema

    async def _format_context(self, user_id: str) -> str:
        """Recupera el historial de la base de datos y lo formatea para el prompt."""
        history = await self.memory.get_history(user_id, limit=10)
        formatted = f"--- MEMORIA PRIVADA ({user_id}) ---\n"
        for msg in history:
            formatted += f"{msg['role'].upper()}: {msg['content']}\n"
        formatted += "--------------------------------------\n"
        return formatted

    async def _build_initial_prompt(self, user_id: str, message: str) -> str:
        """Construye el prompt inicial combinando instrucciones, memoria de trabajo e historial."""
        instructions = self._get_system_instructions()
        context = await self._format_context(user_id)
        
        # Recuperar working memory / core memory formateada
        core_str = await self.core_memory.get_formatted_context(user_id)
        
        return f"{instructions}\n\n{core_str}\n{context}\nTRUTHGPT: "

    def _parse_action(self, response: str) -> AgentAction:
        """Parsea la respuesta en formato JSON de la IA a un objeto AgentAction. Si falla, asume que es texto plano y lo devuelve como final_answer."""
        return parse_agent_action(response)

    async def _run_reflexion(self, user_id: str, current_prompt: str, clean_resp: str, trace_id: str) -> tuple[bool, str]:
        """Evalúa críticamente la respuesta anterior y decide si necesita mejoras."""
        from optimization_core.agents.framework.engines.engines import safe_llm_call
        critique_prompt = (
            f"{current_prompt}\n{clean_resp}\n"
            "[SISTEMA INTERNO]: Evalúa críticamente tu respuesta anterior frente a la petición. "
            "¿Resuelve completamente el problema o la pregunta? "
            "Si la respuesta es perfecta y sin errores, responde EXACTAMENTE '<final>APROBADO</final>'. "
            "Si falta información o hubo un error, escribe tu crítica y planifica el siguiente paso (puedes usar herramientas de nuevo)."
        )
        critique_response = await safe_llm_call(self.llm, critique_prompt, trace_id)
        
        if "<final>APROBADO</final>" in critique_response:
            return True, ""
        return False, critique_response

    async def _finalize_completion(self, user_id: str, message: str, final_answer: str, task_id: str, trace_id: str) -> AgentResponse:
        """Finaliza la ejecución del agente guardando en memoria y actualizando persistencia."""
        # 1. Guardar la respuesta en la memoria del chat (historial)
        await self.memory.add_message(user_id, "assistant", final_answer)

        # 2. RAG Episodic Memory (si está habilitada)
        if self.vector_memory and self.vector_memory.enabled:
            await self.vector_memory.add_episodic(user_id, self.name, f"User: {message}\nAnswer: {final_answer}")
            # Compactar asíncronamente
            from optimization_core.agents.framework.engines.engines import safe_llm_call
            asyncio.create_task(self.vector_memory.compact_episodic_memory(user_id, safe_llm_call))

        # 3. Observabilidad — close trace is handled by the unified loop, but cc_agent_done belongs here
        if CC_AVAILABLE:
            cc_agent_done(self.name, ok=True)

        # 4. Actualizar estado de persistencia/tarea
        if self.persistent:
            from optimization_core.modules.persistence.task_manager import get_persistence_manager
            await get_persistence_manager().mark_completed(task_id)

        return AgentResponse(content=final_answer, action_type="final_answer")

    async def _execute_tool_action(self, trace_id: str, action: AgentAction, user_id: str) -> str:
        """Helper para ejecutar una herramienta y manejar señales internas (Core Memory)."""
        from optimization_core.agents.framework.tools.tools import ToolResult
        
        tool_instance = self.tools[action.tool]
        tool_span = global_tracer.start_span(trace_id, name=action.tool, kind="tool_call", input_data=str(action.tool_input))
        
        try:
            raw_result = await tool_instance.run(str(action.tool_input) or "")
            
            # Handle ToolResult signals
            if isinstance(raw_result, ToolResult):
                result_str = raw_result.output
                if raw_result.signal == "core_memory_append":
                    block = raw_result.metadata.get("block")
                    content = raw_result.metadata.get("content")
                    await self.core_memory.append_to_block(user_id, block, content)
                    result_str = f"SYSTEM: Memoria CORE ({block}) actualizada."
                elif raw_result.signal == "core_memory_replace":
                    block = raw_result.metadata.get("block")
                    content = raw_result.metadata.get("content")
                    await self.core_memory.update_block(user_id, block, content)
                    result_str = f"SYSTEM: Memoria CORE ({block}) remplazada totalmente."
            else:
                result_str = str(raw_result)
                
            tool_span.finish(output=result_str)
            return result_str
            
        except Exception as e:
            from optimization_core.agents.framework.exceptions import ToolExecutionError
            logger.error(f"Error ejecutando {action.tool}: {e}")
            tool_span.finish(output=str(e), status="error")
            raise ToolExecutionError(f"Tool {action.tool} failed: {str(e)}", metadata={"tool": action.tool})

    def _is_dummy_engine(self) -> bool:
        """Comprueba si el motor actual es un DummyFallback."""
        from optimization_core.agents.framework.engines.engine_providers import DummyAsyncLLM
        _engine_obj = self.llm
        _inner = getattr(_engine_obj, "__self__", None)
        if isinstance(_engine_obj, DummyAsyncLLM) or isinstance(_inner, DummyAsyncLLM):
            return True
        _provider_name = getattr(_engine_obj, "provider_name", "") or ""
        _model_name_check = getattr(_engine_obj, "model_name", "") or ""
        return _provider_name == "dummy" or _model_name_check == "dummy-fallback"

    def _is_mock_response(self, response: str) -> bool:
        """Detecta respuestas simuladas de fallback o de error."""
        _resp_stripped = response.strip() if response else ""
        return (
            "Echo from OpenClaw" in _resp_stripped or 
            '"dummy-fallback"' in _resp_stripped or 
            "Motor de inferencia no configurado" in _resp_stripped or 
            "Inference error:" in _resp_stripped
        )

    async def _run_react_loop(self, user_id: str, message: str, task_id: str) -> 'AsyncIterator[Dict[str, Any]]':
        """Unifies the core ReAct execution loop, yielding events as dictionaries."""
        logger.info(f"Iniciando bucle ReAct unificado para {user_id}")
        await self.memory.add_message(user_id, "user", message)

        if self._is_dummy_engine():
            logger.warning("⚠️ DummyAsyncLLM detected — no real LLM engine configured. Aborting ReAct loop.")
            no_engine_msg = (
                "⚠️ Motor de inferencia no configurado. "
                "Configura al menos una API key (DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, "
                "OPENAI_API_KEY, GOOGLE_API_KEY, OPENROUTER_API_KEY) en Settings > Engines."
            )
            await self.memory.add_message(user_id, "assistant", no_engine_msg)
            yield {"event": "final_answer", "content": no_engine_msg, "action_type": "error", "metadata": {"error": "no_engine_configured"}}
            # Record a minimal trace so the issue is visible in traces_history
            _dummy_trace_id = global_tracer.start_trace(
                name="react_loop", agent_name=self.name, input_data=message,
                metadata={"user_id": user_id, "model": "dummy-fallback"},
            )
            global_tracer.finish_trace(
                _dummy_trace_id, output=no_engine_msg, status="no_engine",
                metadata={"iterations": 0, "tool_calls": 0, "errors": 0, "action_type": "no_engine_configured"},
            )
            return
        # ── END GUARD ──

        current_prompt = await self._build_initial_prompt(user_id, message)

        model_name = getattr(self.llm, "model_name", None) or getattr(self.llm, "model", None) or ""
        trace_id = global_tracer.start_trace(
            name="react_loop",
            agent_name=self.name,
            input_data=message,
            metadata={"user_id": user_id, "model": model_name},
        )

        MAX_JSON_RETRIES = 2  # Reduced from 3: faster failure when LLM is broken
        json_retry_count = 0
        total_json_retries = 0  # Track across entire loop for trace metadata
        tool_count = 0
        error_count = 0
        iters_used = 0
        trace_status = "ok"
        trace_output = ""
        trace_extra_meta: Dict[str, Any] = {}

        try:
            actual_iterations = max(60, getattr(settings, "MAX_ITERATIONS", 60))
            for i in range(actual_iterations):
                iters_used = i + 1
                await self._checkpoint(task_id, user_id, message, current_prompt, i)
                yield {"event": "thinking", "iteration": i + 1}

                from optimization_core.agents.framework.engines.engines import safe_llm_call

                async def llm_coro():
                    return await safe_llm_call(self.llm, current_prompt, trace_id)

                try:
                    response = await self.scheduler.execute_with_timeout('planning_agent', llm_coro())
                except Exception as e:
                    logger.error(f"Execution failed or timed out: {e}")
                    error_msg = f"Error de conexión: El motor de inferencia falló o agotó el tiempo (timeout). Detalle: {e}"
                    yield {"event": "final_answer", "content": error_msg, "action_type": "error", "metadata": {"error": "inference_timeout"}}
                    trace_status = "error"
                    trace_output = error_msg
                    trace_extra_meta["action_type"] = "inference_timeout"
                    return

                if self._is_mock_response(response):
                    logger.warning("Mock echo response or inference error detected mid-loop — aborting cascade.")
                    mock_abort_msg = (
                        "⚠️ El motor de inferencia reportó un error o no está configurado. "
                        "Verifica tus API keys en Settings > Engines."
                    )
                    await self.memory.add_message(user_id, "assistant", mock_abort_msg)
                    yield {"event": "final_answer", "content": mock_abort_msg, "action_type": "error", "metadata": {"error": "inference_failure"}}
                    trace_status = "error"
                    trace_output = mock_abort_msg
                    trace_extra_meta["action_type"] = "inference_failure"
                    return
                # ── END GUARD ──

                try:
                    action = self._parse_action(response)
                    clean_resp = response.strip()
                    json_retry_count = 0

                    if action.thought and action.tool and getattr(self, "thought_verification_enabled", True):
                        verification_prompt = (
                            f"Evalúa la lógica de este pensamiento:\n"
                            f"Pensamiento: {action.thought}\n"
                            f"Acción propuesta: {action.tool} -> {action.tool_input}\n"
                            f"Responde estrictamente con un puntaje de confianza de 0.0 a 1.0 (Ej: 0.9). Nada más."
                        )
                        try:
                            verif_res = await safe_llm_call(self.llm, verification_prompt, trace_id)
                            try:
                                verif_score = float(verif_res.strip())
                            except ValueError:
                                verif_score = 1.0
                            if verif_score < 0.7:
                                logger.warning(f"THOUGHT VERIFICATION FAILED: Score {verif_score} for {action.tool}")
                                yield {"event": "thought_verification", "status": "failed", "score": verif_score}
                                result = f"Error interno de razonamiento: Mi propio sistema de verificación calificó este paso con {verif_score}/1.0. Debo repensar la estrategia y probar otra aproximación."
                                yield {"event": "tool_result", "tool": action.tool, "result": result}
                                current_prompt += f"{clean_resp}\nTOOL_RESULT: {result}\nTRUTHGPT: "
                                continue
                        except Exception as e:
                            logger.debug(f"Thought verification skipped: {e}")

                    if action.tool:
                        tool_count += 1
                        if action.tool in self.tools:
                            tool_instance = self.tools[action.tool]
                            if tool_instance.requires_approval:
                                if self.scheduler.can_auto_approve():
                                    logger.warning(f"CIRCUIT BREAKER AUTO-APPROVAL for {action.tool}")
                                    yield {"event": "auto_approval", "tool": action.tool, "cmd": action.tool_input}
                                else:
                                    logger.info(f"HITL PAUSE: Require aprobación para {action.tool}")
                                    yield {"event": "requires_approval", "tool": action.tool, "cmd": action.tool_input, "clean_resp": clean_resp}
                                    approval_msg = f"<WAITING_FOR_APPROVAL tool='{action.tool}' cmd='{action.tool_input}'/>"
                                    await self.memory.add_message(user_id, "assistant", clean_resp)
                                    await self.memory.add_message(user_id, "assistant", f"⏳ Esperando aprobación manual para ejecutar: {action.tool}")
                                    yield {"event": "final_answer", "content": approval_msg, "action_type": "approval_required", "metadata": {"tool": action.tool, "cmd": action.tool_input}}
                                    trace_output = approval_msg
                                    trace_extra_meta["action_type"] = "approval_required"
                                    return

                            if getattr(self, "_memory_optimizer", None) is None:
                                from optimization_core.agents.framework.memory.memory_optimizer import optimizer_instance
                                self._memory_optimizer = optimizer_instance
                                
                            skip, cached_res = self._memory_optimizer.should_skip_redundant_action(action.tool, action.tool_input, user_id)
                            
                            if skip:
                                result = cached_res
                                yield {"event": "tool_call", "tool": action.tool, "cmd": f"(CACHED) {action.tool_input}"}
                            else:
                                yield {"event": "tool_call", "tool": action.tool, "cmd": action.tool_input}
                                if CC_AVAILABLE:
                                    cc_tool_call(f"Executing {action.tool}...")
                                result = await self._execute_tool_action(trace_id, action, user_id)
                                self._memory_optimizer.cache_result(action.tool, action.tool_input, user_id, result)
                                if CC_AVAILABLE:
                                    cc_result(action.tool, note="Success")
                                    cc_tool_output(action.tool, str(result))
                        else:
                            yield {"event": "tool_call", "tool": action.tool, "cmd": action.tool_input}
                            result = f"Error: La herramienta '{action.tool}' no existe."

                        yield {"event": "tool_result", "tool": action.tool, "result": str(result)[:200] + "..."}
                        current_prompt += f"{clean_resp}\nTOOL_RESULT: {result}\nTRUTHGPT: "

                    elif action.final_answer:
                        if self.use_reflexion:
                            yield {"event": "reflexion", "status": "evaluating"}
                            approved, critique = await self._run_reflexion(user_id, current_prompt, clean_resp, trace_id)

                            if approved:
                                yield {"event": "reflexion_approved"}
                                await self._finalize_completion(user_id, message, action.final_answer, task_id, trace_id)
                                yield {"event": "final_answer", "content": action.final_answer, "action_type": "final_answer"}
                                trace_output = action.final_answer
                                trace_extra_meta["action_type"] = "final_answer"
                                return
                            
                            yield {"event": "reflexion_rejected", "critique": critique}
                            current_prompt += f"\n{clean_resp}\n[CRÍTICA]: {critique}\nTRUTHGPT: "
                        else:
                            await self._finalize_completion(user_id, message, action.final_answer, task_id, trace_id)
                            yield {"event": "final_answer", "content": action.final_answer, "action_type": "final_answer"}
                            trace_output = action.final_answer
                            trace_extra_meta["action_type"] = "final_answer"
                            return

                    elif action.handoff:
                        logger.info(f"Iniciando Swarm Handoff hacia: {action.handoff}")
                        yield {"event": "handoff", "target": action.handoff}
                        handoff_msg = f"<HANDOFF target='{action.handoff}'/>"
                        await self.memory.add_message(user_id, "assistant", f"Transferring control to {action.handoff}...")
                        yield {"event": "final_answer", "content": handoff_msg, "action_type": "handoff", "handoff_target": action.handoff}
                        trace_output = handoff_msg
                        trace_extra_meta["action_type"] = "handoff"
                        trace_extra_meta["handoff"] = action.handoff
                        return
                    else:
                        raise ValueError("Debes proveer 'tool', 'final_answer' o 'handoff' en tu JSON.")

                except Exception as e:
                    error_count += 1
                    json_retry_count += 1
                    total_json_retries += 1
                    logger.warning(f"Error parseando Pydantic JSON ({json_retry_count}/{MAX_JSON_RETRIES}): {e}")
                    yield {"event": "error", "message": f"Syntax error recovering ({json_retry_count}/{MAX_JSON_RETRIES})", "is_fatal": False}
                    
                    if json_retry_count >= MAX_JSON_RETRIES:
                        fallback = (
                            "El motor LLM no produjo JSON válido tras varios intentos. "
                            "Por favor reformula tu petición o cambia de motor."
                        )
                        await self.memory.add_message(user_id, "assistant", fallback)
                        yield {"event": "final_answer", "content": fallback, "action_type": "error", "metadata": {"error": "json_retry_exhausted", "total_json_retries": total_json_retries}}
                        trace_status = "error"
                        trace_output = fallback
                        trace_extra_meta["action_type"] = "json_retry_exhausted"
                        trace_extra_meta["total_json_retries"] = total_json_retries
                        return

                    # Only append error correction to prompt if NOT a mock response
                    # (mock engines ignore prompts, so appending is useless pollution)
                    if "Echo from OpenClaw" not in response and "Mock" not in response:
                        current_prompt += (
                            "\n[ERROR DE SISTEMA]: Tu última respuesta no fue JSON válido "
                            "que cumpla el esquema AgentAction. Responde EXACTAMENTE con un objeto JSON "
                            "con los campos 'thought', 'tool', 'tool_input', 'final_answer', sin texto extra.\nTRUTHGPT: "
                        )
                    else:
                        # Mock detected in JSON retry — abort immediately
                        mock_msg = "⚠️ Motor mock detectado durante reintento JSON. Configura un motor real."
                        await self.memory.add_message(user_id, "assistant", mock_msg)
                        yield {"event": "final_answer", "content": mock_msg, "action_type": "error", "metadata": {"error": "mock_in_json_retry"}}
                        trace_status = "error"
                        trace_output = mock_msg
                        trace_extra_meta["action_type"] = "mock_in_json_retry"
                        return

            fallback = "El agente ha procesado extensamente la información pero requiere más detalles para finalizar. ¿Podrías ser más específico con tu petición?"
            await self.memory.add_message(user_id, "assistant", fallback)
            yield {"event": "final_answer", "content": fallback, "action_type": "error", "metadata": {"error": "iteration_limit"}}
            trace_status = "error"
            trace_output = fallback
            trace_extra_meta["action_type"] = "iteration_limit"

        except Exception as outer:
            logger.exception(f"react_loop crashed for user {user_id}")
            trace_status = "error"
            trace_output = f"{type(outer).__name__}: {str(outer)[:200]}"
            trace_extra_meta["action_type"] = "unhandled_exception"
            yield {"event": "error", "message": trace_output, "is_fatal": True}
            raise

        finally:
            global_tracer.finish_trace(
                trace_id,
                output=trace_output,
                status=trace_status,
                metadata={
                    "iterations": iters_used,
                    "tool_calls": tool_count,
                    "errors": error_count,
                    "json_retries": total_json_retries,
                    **trace_extra_meta,
                },
            )

    async def process_message(self, user_id: str, message: str) -> AgentResponse:
        """
        Procesa un mensaje consumiendo el bucle unificado y retornando la respuesta final.
        """
        task_id = str(uuid.uuid4())
        final_resp = None
        
        async for event in self._run_react_loop(user_id, message, task_id):
            if event["event"] == "final_answer":
                final_resp = AgentResponse(
                    content=event["content"],
                    action_type=event.get("action_type", "final_answer"),
                    metadata=event.get("metadata", {}),
                    handoff_target=event.get("handoff_target")
                )
                break
                
        if not final_resp:
            final_resp = AgentResponse(content="Error: loop terminated without final answer.", action_type="error")
            
        return final_resp

    async def astream_process_message(self, user_id: str, message: str) -> 'AsyncIterator[str]':
        """
        Procesa un mensaje emitiendo eventos de Server-Sent Events (SSE) desde el bucle unificado.
        """
        task_id = "streaming_task_" + str(uuid.uuid4())
        
        async for event in self._run_react_loop(user_id, message, task_id):
            if event["event"] == "requires_approval":
                yield json.dumps({"event": "requires_approval", "tool": event["tool"], "cmd": event["cmd"]}) + "\n"
            elif event["event"] == "final_answer":
                yield json.dumps({"event": "final_answer", "content": event["content"]}) + "\n"
                break
            elif event["event"] == "error":
                yield json.dumps({"event": "error", "message": event["message"]}) + "\n"
                if event.get("is_fatal"):
                    break
            elif event["event"] == "handoff":
                yield json.dumps({"event": "handoff", "target": event["target"]}) + "\n"
            else:
                # Eventos intermedios directos (thinking, tool_call, tool_result, reflexion...)
                yield json.dumps(event) + "\n"

    async def resume_task(self, task_id: str) -> AgentResponse:
        """
        Resumes a task from a saved snapshot.
        """
        from optimization_core.modules.persistence.task_manager import get_persistence_manager
        
        snapshot = await get_persistence_manager().load_snapshot(task_id)
        if not snapshot:
            return AgentResponse(content=f"Error: Task {task_id} not found.", action_type="error")
        
        logger.info(f"Resuming task {task_id} for user {snapshot.user_id} at iteration {snapshot.iteration}")
        
        if snapshot.history:
            logger.info(f"Reconstructing chat history ({len(snapshot.history)} messages)...")
            await self.memory.clear_memory(snapshot.user_id)
            await self.memory.bulk_insert_history(snapshot.user_id, snapshot.history)
            
        if snapshot.core_memory:
            logger.info("Restoring Core Working Memory...")
            for block, content in snapshot.core_memory.items():
                await self.core_memory.update_block(snapshot.user_id, block, content)
        
        return await self.process_message(snapshot.user_id, snapshot.metadata.get("original_message", "Resuming task..."))

    async def _checkpoint(self, task_id: str, user_id: str, original_msg: str, prompt: str, iteration: int):
        """Internal helper for state persistence."""
        if not self.persistent:
            return
            
        from optimization_core.modules.persistence.task_manager import get_persistence_manager, TaskSnapshot
            
        history = await self.memory.get_history(user_id, limit=50)
        core_mem = await self.core_memory.get_core(user_id)

        snapshot = TaskSnapshot(
            task_id=task_id,
            user_id=user_id,
            agent_name=self.name,
            current_prompt=prompt,
            iteration=iteration,
            history=history,
            core_memory=core_mem,
            status="running",
            metadata={"original_message": original_msg}
        )
        asyncio.create_task(get_persistence_manager().save_snapshot(snapshot))
