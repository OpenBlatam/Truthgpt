from __future__ import annotations
import logging
import re
import asyncio
import json
import uuid
from typing import List, Dict, Any, Callable, Protocol, Optional, runtime_checkable, Type, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.memoria_aprendizaje.sqlite_memory import SQLiteMemory, BaseMemory
    from agents.memoria_aprendizaje.vector_memory import VectorMemory
    from agents.memoria_aprendizaje.core_memory import CoreMemory
    from agents.razonamiento_planificacion.tools import BaseTool, ToolResult
    from agents.engines import AsyncLLMEngine

from agents.models import AgentAction, AgentResponse, InferenceResult, AgentConfig
from agents.razonamiento_planificacion.config import settings

try:
    from interface.cc_style import (
        cc_action, cc_tool_call, cc_result, cc_agent_done, cc_code_change, cc_tool_output
    )
    CC_AVAILABLE = True
except ImportError:
    CC_AVAILABLE = False

try:
    from agents.observability import global_tracer
except ImportError:
    from ..observability import global_tracer

logger = logging.getLogger(__name__)

# AgentAction and AgentResponse are now imported from .models

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
        tools: Optional[List[BaseTool]] = None
    ):
        from agents.memoria_aprendizaje.sqlite_memory import SQLiteMemory
        from agents.memoria_aprendizaje.core_memory import CoreMemory
        from agents.memoria_aprendizaje.core_memory_tools import CoreMemoryAppendTool, CoreMemoryReplaceTool

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
        from agents.mcp_client import MCPClient
        from agents.razonamiento_planificacion.tools import MCPTool

        logger.info(f"Cargando herramientas MCP desde {server_url}...")
        client = MCPClient(server_url)
        tools_info = await client.list_tools()
        
        for t_info in tools_info:
            mcp_tool = MCPTool(client, t_info)
            self.register_tool(mcp_tool)
        
        logger.info(f"Se cargaron {len(tools_info)} herramientas MCP.")

    def _get_system_instructions(self) -> str:
        """Genera instrucciones dinámicas usando el PromptManager centralizado."""
        from agents.prompts.prompt_manager import prompt_manager
        
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
        """Parsea la respuesta en formato JSON de la IA a un objeto AgentAction."""
        clean_resp = response.strip()
        if clean_resp.startswith("```json"):
            clean_resp = clean_resp[7:-3].strip()
        elif clean_resp.startswith("```"):
            clean_resp = clean_resp[3:-3].strip()
            
        return AgentAction.model_validate_json(clean_resp)

    async def _run_reflexion(self, user_id: str, current_prompt: str, clean_resp: str, trace_id: str) -> tuple[bool, str]:
        """Evalúa críticamente la respuesta anterior y decide si necesita mejoras."""
        from agents.engines import safe_llm_call
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
            from agents.engines import safe_llm_call
            asyncio.create_task(self.vector_memory.compact_episodic_memory(user_id, safe_llm_call))
            
        # 3. Observabilidad
        global_tracer.finish_trace(trace_id)
        if CC_AVAILABLE:
            cc_agent_done(self.name, ok=True)
            
        # 4. Actualizar estado de persistencia/tarea
        if self.persistent:
            from modules.persistence.task_manager import get_persistence_manager
            await get_persistence_manager().mark_completed(task_id)
            
        return AgentResponse(content=final_answer, action_type="final_answer")

    async def process_message(self, user_id: str, message: str) -> AgentResponse:
        """
        Procesa un mensaje de forma asíncrona aislando el contexto por usuario.
        Platinum Edition: Modular, Traced, and Persistent.
        """
        logger.info(f"Iniciando proceso asíncrono para {user_id}")
        await self.memory.add_message(user_id, "user", message)
        
        current_prompt = await self._build_initial_prompt(user_id, message)
        
        # Iniciar traza de observabilidad
        trace_id = global_tracer.start_trace(name="process_message", agent_name="MultiUserReActAgent")
        task_id = str(uuid.uuid4())
        
        for i in range(settings.MAX_ITERATIONS):
            await self._checkpoint(task_id, user_id, message, current_prompt, i)

            # Inferencia asíncrona robusta (con reintentos)
            from agents.engines import safe_llm_call
            response = await safe_llm_call(self.llm, current_prompt, trace_id)
            
            try:
                action = self._parse_action(response)
                clean_resp = response.strip() 
                
                if action.tool:
                    if action.tool in self.tools:
                        tool_instance = self.tools[action.tool]
                        if tool_instance.requires_approval:
                            logger.info(f"HITL PAUSE: Require aprobación para {action.tool}")
                            await self.memory.add_message(user_id, "assistant", clean_resp)
                            await self.memory.add_message(user_id, "assistant", f"⏳ Esperando aprobación manual para ejecutar: {action.tool}")
                            return AgentResponse(
                                content=f"⏳ Esperando aprobación para: {action.tool}",
                                action_type="approval_required",
                                metadata={"tool": action.tool, "cmd": action.tool_input}
                            )
                            
                        if CC_AVAILABLE: cc_tool_call(f"Executing {action.tool}...")
                        result = await self._execute_tool_action(trace_id, action, user_id)
                        if CC_AVAILABLE:
                            cc_result(action.tool, note="Success")
                            cc_tool_output(action.tool, str(result))
                    else:
                        result = f"Error: La herramienta '{action.tool}' no existe."
                    current_prompt += f"{clean_resp}\nTOOL_RESULT: {result}\nTRUTHGPT: "
                    
                elif action.final_answer:
                    if self.use_reflexion:
                        logger.info("Auto-Reflexion: Evaluando respuesta...")
                        approved, critique = await self._run_reflexion(user_id, current_prompt, clean_resp, trace_id)
                        
                        if approved:
                            return await self._finalize_completion(user_id, message, action.final_answer, task_id, trace_id)
                        else:
                            logger.info("Auto-Reflexion: Reintentando tras crítica...")
                            current_prompt += f"\n{clean_resp}\n[CRÍTICA]: {critique}\nTRUTHGPT: "
                    else:
                        return await self._finalize_completion(user_id, message, action.final_answer, task_id, trace_id)
                elif action.handoff:
                    logger.info(f"Iniciando Swarm Handoff hacia: {action.handoff}")
                    await self.memory.add_message(user_id, "assistant", f"Transferring control to {action.handoff}...")
                    return AgentResponse(
                        content=f"Transferring to {action.handoff}...",
                        action_type="handoff",
                        handoff_target=action.handoff
                    )
                else:
                    raise ValueError("Debes proveer 'tool', 'respuesta_final' o 'handoff' en tu JSON.")
                    
            except Exception as e:
                logger.warning(f"Error parseando Pydantic JSON: {e}")
                err_msg = f"Tu respuesta violó el esquema JSON obligatorio. Detalle: {str(e)}"
                current_prompt += f"\n[ERROR DE SISTEMA]: {err_msg}\nCorrige y responde solo en JSON.\nTRUTHGPT: "
        
        fallback = "Límite de razonamiento alcanzado. Por favor, simplifica tu petición."
        await self.memory.add_message(user_id, "assistant", fallback)
        global_tracer.finish_trace(trace_id)
        return AgentResponse(content=fallback, action_type="final_answer")

    from typing import AsyncIterator
    
    async def astream_process_message(self, user_id: str, message: str) -> 'AsyncIterator[str]':
        """
        Procesa un mensaje de forma asíncrona y hace yield de los pasos (Streaming / SSE).
        Emite JSON strings que representan eventos o estados parciales.
        """
        logger.info(f"Iniciando proceso STREAMING para {user_id}")
        await self.memory.add_message(user_id, "user", message)
        
        current_prompt = await self._build_initial_prompt(user_id, message)
        
        trace_id = global_tracer.start_trace(name="astream_process", agent_name="MultiUserReActAgent")
        
        for i in range(settings.MAX_ITERATIONS):
            yield json.dumps({"event": "thinking", "iteration": i+1}) + "\n"
            
            from agents.engines import safe_llm_call
            response = await safe_llm_call(self.llm, current_prompt, trace_id)
            
            try:
                action = self._parse_action(response)
                clean_resp = response.strip()
                
                if action.tool:
                    if action.tool in self.tools:
                        tool_instance = self.tools[action.tool]
                        if tool_instance.requires_approval:
                            logger.info(f"STREAMING HITL PAUSE: Require aprobación para {action.tool}")
                            yield json.dumps({"event": "requires_approval", "tool": action.tool, "cmd": action.tool_input}) + "\n"
                            await self.memory.add_message(user_id, "assistant", clean_resp)
                            approval_msg = f"<WAITING_FOR_APPROVAL tool='{action.tool}' cmd='{action.tool_input}'/>"
                            await self.memory.add_message(user_id, "assistant", f"⏳ Esperando aprobación manual para ejecutar: {action.tool}")
                            yield json.dumps({"event": "final_answer", "content": approval_msg}) + "\n"
                            return
                            
                        yield json.dumps({"event": "tool_call", "tool": action.tool, "cmd": action.tool_input}) + "\n"
                        result = await self._execute_tool_action(trace_id, action, user_id)
                    else:
                        yield json.dumps({"event": "tool_call", "tool": action.tool, "cmd": action.tool_input}) + "\n"
                        result = f"Error: La herramienta '{action.tool}' no existe."
                    
                    yield json.dumps({"event": "tool_result", "tool": action.tool, "result": str(result)[:200] + "..."}) + "\n"
                    current_prompt += f"{clean_resp}\nTOOL_RESULT: {result}\nTRUTHGPT: "
                    
                elif action.final_answer:
                    if self.use_reflexion:
                        yield json.dumps({"event": "reflexion", "status": "evaluating"}) + "\n"
                        approved, critique = await self._run_reflexion(user_id, current_prompt, clean_resp, trace_id)
                        
                        if approved:
                            yield json.dumps({"event": "reflexion_approved"}) + "\n"
                            await self._finalize_completion(user_id, message, action.final_answer, "streaming_task", trace_id)
                            yield json.dumps({"event": "final_answer", "content": action.final_answer}) + "\n"
                            return
                        else:
                            yield json.dumps({"event": "reflexion_rejected", "critique": critique}) + "\n"
                            current_prompt += f"\n{clean_resp}\n[CRÍTICA]: {critique}\nTRUTHGPT: "
                    else:
                        await self._finalize_completion(user_id, message, action.final_answer, "streaming_task", trace_id)
                        yield json.dumps({"event": "final_answer", "content": action.final_answer}) + "\n"
                        return
                elif action.handoff:
                    logger.info(f"STREAMING: Iniciando Swarm Handoff hacia: {action.handoff}")
                    yield json.dumps({"event": "handoff", "target": action.handoff}) + "\n"
                    handoff_msg = f"<HANDOFF target='{action.handoff}'/>"
                    await self.memory.add_message(user_id, "assistant", f"Transferring control to {action.handoff}...")
                    yield json.dumps({"event": "final_answer", "content": handoff_msg}) + "\n"
                    return
                else:
                    raise ValueError("Debes proveer 'tool', 'final_answer' o 'handoff' en tu JSON.")
                    
            except Exception as e:
                logger.warning(f"Error parseando Pydantic JSON: {e}")
                yield json.dumps({"event": "error", "message": f"Syntax error recovering: {str(e)}"}) + "\n"
                current_prompt += f"\n[ERROR DE SISTEMA]: Tu respuesta violó el esquema JSON obligatorio. Detalle: {str(e)}\nCorrige y responde solo en JSON.\nTRUTHGPT: "
        
        fallback = "Límite de razonamiento alcanzado. Por favor, simplifica tu petición."
        await self.memory.add_message(user_id, "assistant", fallback)
        yield json.dumps({"event": "error", "message": fallback}) + "\n"
        global_tracer.finish_trace(trace_id)

    async def _execute_tool_action(self, trace_id: str, action: AgentAction, user_id: str) -> str:
        """Helper para ejecutar una herramienta y manejar señales internas (Core Memory)."""
        from agents.razonamiento_planificacion.tools import ToolResult
        
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
            from agents.exceptions import ToolExecutionError
            logger.error(f"Error ejecutando {action.tool}: {e}")
            tool_span.finish(output=str(e), status="error")
            raise ToolExecutionError(f"Tool {action.tool} failed: {str(e)}", metadata={"tool": action.tool})

    async def resume_task(self, task_id: str) -> AgentResponse:
        """
        Resumes a task from a saved snapshot.
        This is the core of 'running even with the computer off'.
        """
        from modules.persistence.task_manager import get_persistence_manager
        
        snapshot = await get_persistence_manager().load_snapshot(task_id)
        if not snapshot:
            return AgentResponse(content=f"Error: Task {task_id} not found.", action_type="error")
        
        logger.info(f"Resuming task {task_id} for user {snapshot.user_id} at iteration {snapshot.iteration}")
        
        # Platinum Upgrade: State Reconstruction
        if snapshot.history:
            logger.info(f"Reconstructing chat history ({len(snapshot.history)} messages)...")
            await self.memory.clear_memory(snapshot.user_id)
            await self.memory.bulk_insert_history(snapshot.user_id, snapshot.history)
            
        if snapshot.core_memory:
            logger.info("Restoring Core Working Memory...")
            for block, content in snapshot.core_memory.items():
                await self.core_memory.update_block(snapshot.user_id, block, content)
        
        # Continue processing from where it left off
        return await self.process_message(snapshot.user_id, snapshot.metadata.get("original_message", "Resuming task..."))

    async def _checkpoint(self, task_id: str, user_id: str, original_msg: str, prompt: str, iteration: int):
        """Internal helper for state persistence."""
        if not self.persistent:
            return
            
        from modules.persistence.task_manager import get_persistence_manager, TaskSnapshot
            
        # Platinum Upgrade: Full state capture
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
        # Non-blocking async save
        asyncio.create_task(get_persistence_manager().save_snapshot(snapshot))

