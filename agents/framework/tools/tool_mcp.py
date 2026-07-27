import json
from typing import Any, Dict
from .tool_base import BaseTool

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
