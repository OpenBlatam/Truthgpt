import asyncio
import logging
from .tool_base import BaseTool

logger = logging.getLogger(__name__)

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
