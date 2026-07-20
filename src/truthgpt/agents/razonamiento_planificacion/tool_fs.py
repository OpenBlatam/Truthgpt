import os
import json
import logging
from .tool_base import BaseTool

logger = logging.getLogger(__name__)

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
                    from truthgpt.interface.cc_style import cc_code_change
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
                from truthgpt.interface.cc_style import cc_code_change
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
