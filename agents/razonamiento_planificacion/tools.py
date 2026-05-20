"""
System 5.9 — Agent Tools.

BaseTool ABC and built-in tool implementations for the ReAct agent loop.
"""

import os
import sys
import json
import asyncio
import subprocess
import logging
import re
import httpx
from typing import Any, Callable, Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ToolResult:
    """
    Standardized result from a tool execution.
    Can contain the final output string and optional internal signals for the orchestrator.
    """
    def __init__(
        self, 
        output: str, 
        metadata: Optional[Dict[Any, Any]] = None, 
        signal: Optional[str] = None
    ):
        self.output = output
        self.metadata = metadata or {}
        self.signal = signal  # e.g., "core_memory_update"

class BaseTool(ABC):
    """
    Clase base para herramientas automatizadas. 
    Permite que el agente obtenga la descripción automáticamente del docstring.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre único de la herramienta."""
        pass

    @property
    def description(self) -> str:
        """Description extracted from the docstring for LLM consumption."""
        return self.__doc__.strip() if self.__doc__ else "No description available."
        
    @property
    def risk_level(self) -> str:
        """Risk level (LOW, MEDIUM, HIGH) for execution permission handling."""
        return "LOW"
        
    @property
    def requires_approval(self) -> bool:
        """Si es True, la ejecución requerirá aprobación manual del usuario (HITL)."""
        return self.risk_level == "HIGH"

    @abstractmethod
    async def run(self, arg: str) -> Any:
        """
        Ejecución asíncrona de la herramienta. 
        Puede devolver un string simple o un objeto ToolResult.
        """
        pass

# --- System Tools ---

class SystemBashTool(BaseTool):
    """
    Executes terminal commands (bash/shell) safely.
    Integrates heuristic risk-classification and regex-based threat prevention
    to block reverse shells, privilege escalation, and destructive operations.
    """
    name = "system_bash"
    
    # Pre-compile security patterns for performance
    _SECURITY_PATTERNS = [
        re.compile(p, re.IGNORECASE) for p in [
            r"\bsudo\b", r"\bsu\b\s+-", r"\bchown\b", r"\bchmod\b\s+777",
            r"\brm\b\s+-rf\s+/", r"\bmv\b.*(?:\/dev\/null)", r"\b>/dev/sda",
            r"\bmkfs\b", r"\bdd\s+if=", r"\bnetcat\b", r"\bnc\b\s+-e",
            r"\bbash\b\s+-i", r"\bsh\b\s+-i", r"\bperl\b\s+-e\s+.*socket",
            r"\bpython\b\s+-c\s+.*pty", r"\bruby\b\s+-rsocket", r"\bphp\b\s+-r",
            r"\bawf\b\s+.*\/dev\/tcp", r"\bcurl\b.*\|.*bash", r"\bwget\b.*\|.*sh",
            r"\b:?\(\)\{",  # fork bomb
            r"\/etc\/(passwd|shadow|sudoers)", r"\.ssh\/(id_rsa|authorized_keys)"
        ]
    ]
    
    @property
    def risk_level(self) -> str:
        return "HIGH"

    def _yolo_auto_approve(self, cmd: str) -> bool:
        """Heuristic to auto-approve harmless read-only commands."""
        safe_prefixes = ["ls", "pwd", "echo", "cat", "whoami", "git status", "git diff", "node --version", "python --version"]
        return any(cmd.strip().startswith(prefix) for prefix in safe_prefixes) and "|" not in cmd and ">" not in cmd

    async def run(self, cmd: str) -> str:
        # Pre-execution Security Audit
        for pattern in self._SECURITY_PATTERNS:
            if pattern.search(cmd):
                logger.error("[Security Policy] FATAL: Command matched blocked pattern: %s", pattern.pattern)
                return "Error: Command classified as CRITICAL (Reverse Shell, PrivEsc, or Destructive). Execution blocked."
        
        if self._yolo_auto_approve(cmd):
            logger.info("[Auto-Approve] Safe command authorized: %s", cmd)
            
        process = None
        try:
            # Execute in isolated subprocess (PTY emulation safety via subprocess.PIPE)
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=15.0)
            
            output = stdout.decode('utf-8', errors='replace')
            
            # Context Limits & Output Truncation
            # Prevents massive outputs from overflowing the LLM context window:
            MAX_CHARS = 8000
            if len(output) > MAX_CHARS:
                half = MAX_CHARS // 2
                output = (
                    output[:half] + 
                    "\n\n... [TRUNCATED: Output exceeded Context Window limits. Showing head and tail] ...\n\n" + 
                    output[-half:]
                )
            
            return output if output.strip() else "[Command executed with no output]"
            
        except asyncio.TimeoutError:
            if process:
                try:
                    process.terminate()
                except Exception:
                    pass
            return "Error: Command exceeded execution timeout of 15s."
        except Exception as e:
            return f"System exception: {str(e)}"
        finally:
            # PTY File Descriptor Leak Prevention
            if process and process.returncode is None:
                try:
                    process.kill()
                except Exception:
                    pass

# --- Herramientas Web ---

class WebSearchTool(BaseTool):
    """
    Web search via DuckDuckGo with automatic degradation.

    Strategies (in order):
    1. ``duckduckgo_search`` library
    2. HTTP fallback to DuckDuckGo Lite
    3. Graceful degradation advisory after *_DEGRADED_THRESHOLD* consecutive failures
    """

    name = "web_search"
    _DEGRADED_THRESHOLD = 3

    def __init__(self) -> None:
        self._failures: int = 0

    async def run(self, query: str) -> str:
        logger.info("web_search: %s", query)

        if self._failures >= self._DEGRADED_THRESHOLD:
            return (
                f"[TOOL DEGRADED] web_search ha fallado {self._failures} "
                f"veces consecutivas. Usa tu conocimiento interno. "
                f"Query: '{query}'"
            )

        # Strategy 1: duckduckgo_search library
        result = await self._try_ddgs(query)
        if result is not None:
            return result

        # Strategy 2: HTTP fallback
        result = await self._try_http(query)
        if result is not None:
            return result

        # All failed
        self._failures += 1
        return (
            f"Sin resultados para '{query}'. "
            f"[Fallos: {self._failures}/{self._DEGRADED_THRESHOLD}]. "
            f"Usa tu conocimiento interno."
        )

    async def _try_ddgs(self, query: str) -> Optional[str]:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=5))
                if hits:
                    self._failures = 0
                    lines = [
                        f"{i}. **{h.get('title', '—')}**\n"
                        f"   {h.get('body', '')}\n"
                        f"   Link: {h.get('href', 'N/A')}"
                        for i, h in enumerate(hits, 1)
                    ]
                    return f"Resultados para '{query}':\n\n" + "\n\n".join(lines)
        except ImportError:
            logger.info("duckduckgo_search not installed, trying HTTP.")
        except Exception as exc:
            logger.warning("DDGS failed: %s", exc)
        return None

    async def _try_http(self, query: str) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://lite.duckduckgo.com/lite/",
                    params={"q": query},
                    headers={"User-Agent": "TruthGPT/5.9"},
                )
                if resp.status_code == 200 and len(resp.text) > 500:
                    self._failures = 0
                    return f"Resultados (raw) para '{query}':\n{resp.text[:2000]}"
        except Exception as exc:
            logger.warning("HTTP fallback failed: %s", exc)
        return None

class WebReaderTool(BaseTool):
    """
    Lee el contenido textual de una URL específica usando Crawl4AI. 
    Extrae texto limpio y estructurado en Markdown perfecto para el LLM.
    """
    name = "web_reader"

    async def run(self, url: str) -> str:
        if not url.startswith("http"):
            return "Error: URL inválida."
            
        try:
            from crawl4ai import AsyncWebCrawler
            
            logger.info(f"Crawling URL con Crawl4AI: {url}")
            async with AsyncWebCrawler(verbose=True) as crawler:
                result = await crawler.arun(url=url)
                
                if result.success:
                    # Return perfectly formatted markdown
                    markdown = result.markdown
                    return markdown[:5000] + "\n...[Truncated]" if len(markdown) > 5000 else markdown
                else:
                    return f"Error al crawlear: {result.error_message}"
                    
        except ImportError:
            # Fallback to bs4 if crawl4ai is not installed
            logger.warning("crawl4ai no instalado. Usando fallback bs4.")
            try:
                import bs4
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    soup = bs4.BeautifulSoup(response.text, "html.parser")
                    text = soup.get_text(separator="\n", strip=True)
                    return text[:5000]
            except Exception as e:
                return f"Error en fallback bs4: {str(e)}"
        except Exception as e:
            return f"Error inesperado en WebReaderTool: {str(e)}"

# --- Herramientas de Sistema de Archivos y Código ---

class FileReadTool(BaseTool):
    """
    Lee el contenido de un archivo local.
    Acepta la ruta absoluta o relativa del archivo y devuelve su contenido.
    """
    name = "file_read"

    async def run(self, filepath: str) -> str:
        filepath = filepath.strip()
        if filepath.startswith("{"):
            try:
                d = json.loads(filepath)
                if isinstance(d, dict):
                    filepath = d.get("filepath") or d.get("path") or d.get("file") or filepath
            except Exception:
                pass
        try:
            if not os.path.exists(filepath):
                return f"Error: El archivo '{filepath}' no existe."
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()[:5000]  # Limitar a 5000 caracteres
        except Exception as e:
            return f"Error al leer archivo: {str(e)}"

class DirectoryListTool(BaseTool):
    """
    Lista los archivos y subdirectorios en una ruta local.
    Acepta la ruta del directorio.
    """
    name = "directory_list"

    async def run(self, path: str) -> str:
        path = path.strip()
        if path.startswith("{"):
            try:
                d = json.loads(path)
                if isinstance(d, dict):
                    path = d.get("path") or d.get("directory") or d.get("dir") or path
            except Exception:
                pass
        try:
            if not os.path.exists(path):
                return f"Error: El directorio '{path}' no existe."
            if not os.path.isdir(path):
                return f"Error: '{path}' no es un directorio."
            
            items = os.listdir(path)
            # Diferenciar entre archivos y carpetas
            result = []
            for item in items:
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    result.append(f"[DIR] {item}")
                else:
                    result.append(f"[FILE] {item}")
            
            return "\n".join(result) if result else "Directorio vacío."
        except Exception as e:
            return f"Error al listar directorio: {str(e)}"

class GlobTool(BaseTool):
    """
    Searches for files matching a specific glob pattern (e.g., src/**/*.py).
    Designed to avoid executing raw bash search commands.
    """
    name = "glob_search"
    
    @property
    def risk_level(self) -> str:
        return "LOW"

    async def run(self, pattern: str) -> str:
        import glob
        try:
            # Basic protections against full disk scans
            if pattern in ["*", "/*", "C:\\*"] or pattern.count("*") > 5:
                return "Error: Glob pattern is too broad or risky."
                
            matches = glob.glob(pattern, recursive=True)
            if not matches:
                return f"No files found for pattern '{pattern}'."
                
            # Limit results to prevent context bloating
            limit = 100
            result = "\n".join(matches[:limit])
            if len(matches) > limit:
                result += f"\n... and {len(matches) - limit} more hidden results."
            return result
        except Exception as e:
            return f"Glob search error: {str(e)}"

class FileWriteTool(BaseTool):
    """
    Edits or writes content to a local file.
    
    To replace specific strings (Exact str_replace mechanism):
    {"path": "...", "old_string": "...", "new_string": "..."}
    
    To overwrite the entire file:
    {"path": "...", "content": "..."}
    """
    name = "file_write"

    async def run(self, cmd: str) -> str:
        parsed = self._parse(cmd)
        if isinstance(parsed, tuple) and parsed[0] is None:
            return parsed[1]  # error
        
        filepath = parsed.get("path")
        content = parsed.get("content")
        old_string = parsed.get("old_string")
        new_string = parsed.get("new_string")
        
        if not filepath:
            return "Error: filepath is required."
            
        try:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            action_name = "Update"
            old_content = ""
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as fh:
                    old_content = fh.read()
            else:
                action_name = "Create"
                
            if old_string is not None and new_string is not None:
                # Exact string replacement
                if old_content.count(old_string) == 0:
                    return "Error: old_string not found in file. Ensure exact match including whitespace and line endings."
                if old_content.count(old_string) > 1:
                    return "Error: old_string matches multiple times. Provide more context to make it unique."
                
                final_content = old_content.replace(old_string, new_string)
            else:
                # Overwrite entire file
                final_content = content
                
            import difflib
            old_lines = old_content.splitlines()
            new_lines = final_content.splitlines()
            diff_gen = difflib.unified_diff(old_lines, new_lines, fromfile=filepath, tofile=filepath, lineterm="")
            diff_list = list(diff_gen)
            
            if diff_list:
                added = sum(1 for line in diff_list if line.startswith('+') and not line.startswith('+++'))
                removed = sum(1 for line in diff_list if line.startswith('-') and not line.startswith('---'))
                diff_text = "\n".join(diff_list[2:])  # Skip headers
                try:
                    from interface.cc_style import cc_code_change
                    cc_code_change(
                        action=action_name,
                        path=filepath,
                        added=added,
                        removed=removed,
                        diff_text=diff_text
                    )
                except ImportError:
                    pass

            with open(filepath, "w", encoding="utf-8") as fh:
                fh.write(final_content)
            return f"Success: File updated at '{filepath}'."
        except Exception as exc:
            return f"File write error: {exc}"

    @staticmethod
    def _parse(cmd: str):
        stripped = cmd.strip()

        if stripped.startswith("{"):
            try:
                d = json.loads(stripped)
                if isinstance(d, dict):
                    fp = d.get("path") or d.get("filepath") or d.get("file")
                    if fp:
                        if "old_string" in d and "new_string" in d:
                            return {"path": fp.strip(), "old_string": d["old_string"], "new_string": d["new_string"]}
                        ct = d.get("content") or d.get("text") or d.get("data")
                        if ct is not None:
                            return {"path": fp.strip(), "content": ct}
            except (json.JSONDecodeError, TypeError):
                pass

        parts = cmd.split(":::", 1)
        if len(parts) == 2:
            return {"path": parts[0].strip(), "content": parts[1]}

        return (None, "Error: Invalid format.")

class NotebookEditTool(BaseTool):
    """
    Safely edits Jupyter Notebooks (.ipynb) by cell index.
    Expects JSON: {"path": "notebook.ipynb", "cell_index": 0, "source": "print('hello')"}
    """
    name = "notebook_edit"
    
    @property
    def risk_level(self) -> str:
        return "MEDIUM"

    async def run(self, cmd: str) -> str:
        import json
        import os
        try:
            d = json.loads(cmd.strip())
            path = d.get("path")
            cell_index = d.get("cell_index")
            source = d.get("source")
            
            if not path or cell_index is None or source is None:
                return "Error: Required fields: 'path', 'cell_index', 'source'"
                
            if not os.path.exists(path):
                return f"Error: Notebook {path} not found."
                
            with open(path, "r", encoding="utf-8") as f:
                notebook = json.load(f)
                
            cells = notebook.get("cells", [])
            if cell_index < 0 or cell_index >= len(cells):
                return f"Error: Cell index out of bounds. Notebook has {len(cells)} cells."
                
            # Update cell source
            old_source = "".join(cells[cell_index].get("source", []))
            
            cells[cell_index]["source"] = [line + "\n" for line in source.split("\n")]
            cells[cell_index]["source"][-1] = cells[cell_index]["source"][-1].rstrip("\n") # Fix last line
            
            new_source = "".join(cells[cell_index]["source"])
            
            # Reset outputs for execution safety
            if "outputs" in cells[cell_index]:
                cells[cell_index]["outputs"] = []
            if "execution_count" in cells[cell_index]:
                cells[cell_index]["execution_count"] = None
                
            with open(path, "w", encoding="utf-8") as f:
                json.dump(notebook, f, indent=1)
                
            # Log visual diff in terminal
            try:
                import difflib
                from interface.cc_style import cc_code_change
                old_lines = old_source.splitlines()
                new_lines = new_source.splitlines()
                diff_gen = difflib.unified_diff(old_lines, new_lines, fromfile=f"Cell {cell_index}", tofile=f"Cell {cell_index}", lineterm="")
                diff_list = list(diff_gen)
                if diff_list:
                    added = sum(1 for line in diff_list if line.startswith('+') and not line.startswith('+++'))
                    removed = sum(1 for line in diff_list if line.startswith('-') and not line.startswith('---'))
                    diff_text = "\n".join(diff_list[2:])
                    cc_action_name = "Update Cell"
                    cc_code_change(action=cc_action_name, path=path, added=added, removed=removed, diff_text=diff_text)
            except ImportError:
                pass
                
            return f"Success: Cell {cell_index} updated in {path}."
        except Exception as e:
            return f"Notebook edit error: {str(e)}"

class PythonExecutionTool(BaseTool):
    """
    Ejecuta código Python de forma asíncrona dentro de un contenedor Docker aislado (Sandbox).
    Acepta código fuente en Python y devuelve la salida.
    """
    name = "python_execute"
    
    @property
    def requires_approval(self) -> bool:
        return True

    async def run(self, code: str) -> str:
        try:
            import docker
            from docker.errors import ContainerError, ImageNotFound, APIError
            
            client = docker.from_env()
            
            def _run_docker_securely():
                # Pull image if not exists
                try:
                    client.images.get("python:3.9-slim")
                except ImageNotFound:
                    logger.info("Descargando imagen python:3.9-slim para el sandbox...")
                    client.images.pull("python:3.9-slim")

                # Ejecutar de forma segura usando un contenedor efímero
                result = client.containers.run(
                    "python:3.9-slim",
                    command=["python", "-c", code],
                    remove=True,
                    network_mode="none", # Aislar red
                    mem_limit="128m",    # Limitar memoria
                    stderr=True,
                    stdout=True
                )
                return result.decode("utf-8")
                
            output = await asyncio.to_thread(_run_docker_securely)
            return output[:5000] if output else "Ejecutado sin salida."
            
        except ImportError:
            return "Error: La librería 'docker' no está instalada. Instala con 'pip install docker'."
        except Exception as e:
            return f"Error en el Sandbox de Docker: {str(e)}"


# --- Herramientas de Delegación (Multi-Agente) ---

class DelegateTaskTool(BaseTool):
    """
    Delega una sub-tarea compleja a otro agente del enjambre.
    Acepta el nombre del agente y la tarea en formato 'agente:::tarea_a_completar'.
    Ejemplo: MarketingAgent:::Escribe un tweet sobre este resumen.
    Si no sabes qué agente usar, usa 'swarm', ej: swarm:::Crea un reporte de estos datos.
    """
    name = "delegate_task"

    def __init__(self, agent_client: Any = None):
        """Require AgentClient instance to allow recursive calling."""
        self.agent_client = agent_client

    async def run(self, cmd: str) -> str:
        if not self.agent_client:
            return "Error: DelegateTaskTool requiere una instancia de AgentClient."
            
        try:
            parts = cmd.split(":::", 1)
            if len(parts) != 2:
                return "Error: Formato inválido. Use 'agente:::tarea'."
            
            agent_target, task = parts
            agent_target = agent_target.strip()
            task = task.strip()
            
            logger.info(f"Delegando tarea a '{agent_target}': {task[:50]}...")
            
            # Isolated sub-memory namespace for the delegated task
            sub_user_id = f"delegate_{agent_target}_temp"
            
            # Run the task through the orchestrator/client
            # This allows hierarchical agent branching!
            result = await self.agent_client.run(user_id=sub_user_id, prompt=task)
            return f"Respuesta de {agent_target}:\n{result}"
        except Exception as e:
            return f"Error en delegación de tarea: {str(e)}"

# --- Herramientas de Interoperabilidad (MCP) ---

class MCPTool(BaseTool):
    """
    Wrapper para herramientas externas del Model Context Protocol (MCP).
    Permite usar herramientas servidas por un MCP Server remoto.
    """
    def __init__(self, mcp_client: Any, tool_info: Dict[str, Any]):
        self.mcp_client = mcp_client
        self._name = tool_info["name"]
        self._description = tool_info.get("description", "No description available via MCP.")
        self.arguments_schema = tool_info.get("inputSchema", {})

    @property
    def name(self) -> str:
        return f"mcp_{self._name}"

    @property
    def description(self) -> str:
        return f"[MCP Tool] {self._description}\nSchema: {json.dumps(self.arguments_schema)}"

    async def run(self, arg: str) -> str:
        """
        Ejecuta la herramienta MCP. Intenta parsear JSON si la herramienta lo requiere.
        """
        try:
            # MCP tools often expect a JSON object for arguments
            try:
                args_dict = json.loads(arg)
            except json.JSONDecodeError:
                args_dict = {"input": arg} # Fallback simple
                
            result = await self.mcp_client.call_tool(self._name, args_dict)
            return str(result)
        except Exception as e:
            return f"Error executing MCP tool '{self._name}': {str(e)}"

