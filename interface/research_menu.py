"""
SOTA Research & Deep Discovery Hub
"""
import time
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from interface.core import (
    console, USER_PREFS, clear_screen, get_header, wait_for_user
)
from interface.cc_style import cc_menu, cc_step

@cc_menu("SOTA Research & Deep Discovery")
async def research_menu():
    from modules.base.core_system.core.papers.paper_registry import get_paper_registry
    registry = get_paper_registry(preload_popular=False)
    while True:
        clear_screen()
        console.print(get_header())
        papers = registry.list_papers()[:10]
        console.print(f" [bold magenta]SOTA Trend Radar:[/bold magenta] [dim]{len(papers)} papers indexed[/dim]")
        for i, p in enumerate(papers, 1):
            console.print(f" {i:2} | [magenta]{p.paper_id:25}[/magenta] | [green]{p.category}[/green]")
        console.print(" [bold white]D[/bold white] | Autonomous Discovery (ArXiv)")
        console.print(" [bold white]T[/bold white] | Tavily Neural Search (SOTA)")
        console.print(" [bold white]M[/bold white] | Mathematical Discovery (Erdos Solver)")
        console.print(" [bold white]0[/bold white] | Return")
        choice = Prompt.ask("Selection").upper()
        if choice == "0": break
        elif choice.isdigit() and 1 <= int(choice) <= len(papers):
            selected = papers[int(choice)-1]
            clear_screen()
            console.print(Panel(f"[bold magenta]Paper Selection:[/bold magenta] {selected.paper_id}", border_style="magenta"))
            console.print(f"[bold]Title:[/bold] {selected.title}")
            console.print(f"[bold]Category:[/bold] {selected.category}")
            console.print(f"[bold]ArXiv ID:[/bold] {getattr(selected, 'arxiv_id', 'N/A')}")
            
            action = Prompt.ask("\n[1] View Info [2] Apply/Execute [0] Back", choices=["0", "1", "2"])
            if action == "1":
                from optimization_core.modules.base.core_system.core.papers.paper_registry import PaperRegistry
                registry = PaperRegistry()
                paper = next((p for p in registry.list_papers() if p.paper_id == selected.paper_id), None)
                if paper:
                    link = f"https://arxiv.org/abs/{paper.arxiv_id}" if getattr(paper, 'arxiv_id', None) else "N/A"
                    console.print(Panel(f"[bold]Paper ID:[/bold] {paper.paper_id}\n[bold]Category:[/bold] {paper.category}\n[bold]SOTA Link:[/bold] {link}\n[bold]Techniques:[/bold] {', '.join(paper.key_techniques) if getattr(paper, 'key_techniques', None) else 'N/A'}\n[bold]Speedup:[/bold] {getattr(paper, 'speedup', '1.0')}x\n[bold]Accuracy:[/bold] +{getattr(paper, 'accuracy_improvement', '0.0')}%", title=f"📄 Paper: {paper.title}", border_style="magenta"))
                wait_for_user(force=True)
            elif action == "2":
                import subprocess
                import sys
                from pathlib import Path
                with console.status(f"[bold magenta]Applying Paper {selected.paper_id}...[/bold magenta]"):
                    p_id_clean = selected.paper_id.replace(".", "_").replace("-", "_")
                    script_path = Path(f"optimization_core/truthgpt_collected/integration_code/papers/research/paper_{p_id_clean}.py")
                    if not script_path.exists():
                        from agents.system_intelligence.system_tools import PaperSynthesisTool
                        synthesis = PaperSynthesisTool()
                        await synthesis.run(f"{selected.paper_id}:::{selected.title}:::{selected.category}:::N/A")
                    
                    try:
                        result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, timeout=30)
                        success, output = result.returncode == 0, result.stdout + result.stderr
                    except Exception as e: success, output = False, str(e)
                
                if success:
                    console.print(Panel(f"[bold green]✓ Paper Applied Successfully[/bold green]\n\n{output[-500:]}", border_style="green"))
                else:
                    console.print(Panel(f"[bold red]✗ Application Failed[/bold red]\n\n{output}", border_style="red"))
                wait_for_user(force=True)

        elif choice == "D":
            query = Prompt.ask("Search ArXiv (e.g., 'Transformer Optimization')")
            
            # --- Perform ArXiv Search ---
            import httpx
            import xml.etree.ElementTree as ET
            from rich.table import Table
            
            with console.status(f"[bold magenta]Searching ArXiv for '{query}'...[/bold magenta]"):
                search_query = f"all:{query.replace(' ', '+')}"
                url = f"https://export.arxiv.org/api/query?search_query={search_query}&max_results=10"
                try:
                    import httpx
                    response = httpx.get(url, timeout=15)
                    root = ET.fromstring(response.text)
                    ns = {'atom': 'http://www.w3.org/2005/Atom'}
                    found_papers = []
                    for entry in root.findall('atom:entry', ns):
                        title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                        arxiv_id = entry.find('atom:id', ns).text.split('/')[-1]
                        category = entry.find('atom:category', ns).attrib['term']
                        found_papers.append({"id": arxiv_id, "title": title, "category": category})
                except Exception as e:
                    console.print(f"[red]Error searching ArXiv: {e}[/red]")
                    wait_for_user(force=True)
                    continue

            if not found_papers:
                console.print("[yellow]No papers found for that query.[/yellow]")
                wait_for_user(force=True)
                continue

            clear_screen()
            console.print(Panel(f"[bold magenta]ArXiv Search Results for:[/bold magenta] {query}", border_style="magenta"))
            
            results_table = Table(box=None)
            results_table.add_column("Idx", style="dim", width=4)
            results_table.add_column("ID", style="cyan", width=15)
            results_table.add_column("Title", style="white")
            
            for i, p in enumerate(found_papers, 1):
                results_table.add_row(str(i), p["id"], p["title"])
            
            console.print(results_table)
            
            sub_choice = Prompt.ask("\nEnter # to adopt, a new query, or '0' to return")
            
            if sub_choice == "0": continue
            
            target_paper = None
            if sub_choice.isdigit() and 1 <= int(sub_choice) <= len(found_papers):
                target_paper = found_papers[int(sub_choice)-1]
                paper_id = target_paper["id"]
                paper_title = target_paper["title"]
            else:
                # If they typed a paper ID directly or something else
                paper_id = sub_choice
                paper_title = f"Manual Discovery: {paper_id}"

            if paper_id:
                from agents.system_intelligence.system_tools import PaperSynthesisTool, SOTAPaperScraperTool
                with console.status(f"[bold cyan]Scraping Paper {paper_id}...[/bold cyan]"):
                    scraper = SOTAPaperScraperTool()
                    scrape_res = await scraper.run(paper_id)
                    console.print(f"[dim]{scrape_res}[/dim]")
                
                with console.status(f"[bold green]Synthesizing Implementation for {paper_id}...[/bold green]"):
                    synthesis = PaperSynthesisTool()
                    synth_res = await synthesis.run(f"{paper_id}:::{paper_title}:::Deep Learning:::Synthesized from ArXiv Discovery")
                    console.print(Panel(synth_res, title="Integration Result", border_style="green"))
                wait_for_user(force=True)

        elif choice == "M":
            from modules.math.erdos_solver import ErdosSolver
            solver = ErdosSolver()
            solver.forensic_report()
            wait_for_user(force=True)
        elif choice == "T":
            query = Prompt.ask("Research Query")
            console.print(f"[cyan]➤ Querying Tavily for {query}...[/cyan]")
            time.sleep(1)
            wait_for_user(force=True)

@cc_menu("Intelligence Labs")
async def intelligence_labs_menu():
    labs = [("Data Analysis", "data_expert"), ("Reasoning Lab", "reasoning_agent")]
    while True:
        clear_screen()
        console.print(get_header())
        lab_table = Table(title="🧠 Intelligence Labs")
        for i, (name, _) in enumerate(labs, 1): lab_table.add_row(str(i), name)
        console.print(lab_table)
        choice = Prompt.ask("Selection", choices=["0", "1", "2"])
        if choice == "0": break
        # ... logic ...
        wait_for_user(force=True)
