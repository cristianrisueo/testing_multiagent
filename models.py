from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from enum import Enum
import uuid
from fastapi import HTTPException
from .config import app_logger as logger


# Excepciones personalizadas
class AgentException(Exception):
    """Excepción base para errores relacionados con agentes"""

    pass


class AgentNotAvailableError(AgentException):
    """Excepción cuando un agente solicitado no está disponible"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.message = f"Agente no disponible: {agent_name}"
        super().__init__(self.message)


class AgentStartupError(AgentException):
    """Excepción cuando hay un error al iniciar un agente"""

    def __init__(self, agent_name: str, details: str = ""):
        self.agent_name = agent_name
        self.details = details
        self.message = f"Error al iniciar el agente {agent_name}"
        if details:
            self.message += f": {details}"
        super().__init__(self.message)


class AgentShutdownError(AgentException):
    """Excepción cuando hay un error al detener un agente"""

    def __init__(self, agent_id: str, details: str = ""):
        self.agent_id = agent_id
        self.details = details
        self.message = f"Error al detener el agente con ID {agent_id}"
        if details:
            self.message += f": {details}"
        super().__init__(self.message)


class AgentNotFoundError(AgentException):
    """Excepción cuando no se encuentra un agente"""

    def __init__(self, criteria: str):
        self.criteria = criteria
        self.message = (
            f"No se encontraron agentes que coincidan con los criterios: {criteria}"
        )
        super().__init__(self.message)


class AgentAlreadyRunningError(AgentException):
    """Excepción cuando se intenta iniciar un agente que ya está en ejecución"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.message = f"El agente {agent_name} ya está en ejecución"
        super().__init__(self.message)


# Función para convertir excepciones personalizadas a HTTPExceptions
def agent_exception_handler(exc: AgentException) -> HTTPException:
    """Convierte excepciones de agente a HTTPExceptions"""

    if isinstance(exc, AgentNotAvailableError):
        logger.warning("Agente solicitado no disponible: %s", exc.agent_name)
        return HTTPException(status_code=400, detail=exc.message)

    elif isinstance(exc, AgentStartupError):
        logger.error("Error al iniciar agente %s: %s", exc.agent_name, exc.details)
        return HTTPException(status_code=500, detail=exc.message)

    elif isinstance(exc, AgentShutdownError):
        logger.error("Error al detener agente con ID %s: %s", exc.agent_id, exc.details)
        return HTTPException(status_code=500, detail=exc.message)

    elif isinstance(exc, AgentNotFoundError):
        logger.warning("Agente no encontrado: %s", exc.criteria)
        return HTTPException(status_code=404, detail=exc.message)

    elif isinstance(exc, AgentAlreadyRunningError):
        logger.warning("Agente ya en ejecución: %s", exc.agent_name)
        return HTTPException(status_code=409, detail=exc.message)

    # Excepción genérica para otros casos
    logger.error("Error inesperado de agente: %s", str(exc))
    return HTTPException(status_code=500, detail=str(exc))


# Modelos Pydantic
class AgentStatus(str, Enum):
    """Estados posibles para un agente"""

    RUNNING = "running"
    STARTING = "starting"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class SharepointConfig(BaseModel):
    """Configuración para recursos de Sharepoint"""

    url: str
    user: str
    password: str


class ManifestPayload(BaseModel):
    """Payload para la creación de agentes"""

    agents: List[str]
    resources: Dict[str, Any]


class AgentInfo(BaseModel):
    """Información de un agente en ejecución"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    pid: int
    port: int
    status: AgentStatus = AgentStatus.RUNNING
    start_time: float


class AgentResponse(BaseModel):
    """Respuesta de la API para operaciones con agentes"""

    id: str
    name: str
    pid: int
    port: int
    status: AgentStatus
    start_time: float

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "f8c3de3d-1fea-4d7c-a8b0-29f63c4c3454",
                "name": "vfs",
                "pid": 12345,
                "port": 8001,
                "status": "running",
                "start_time": 1618037123.456,
            }
        }
    }


class AgentListResponse(BaseModel):
    """Respuesta para listar agentes"""

    agents: List[AgentResponse]


class AgentLaunchResponse(BaseModel):
    """Respuesta para lanzamiento de agentes"""

    launched_agents: List[AgentResponse]


class AgentStopResponse(BaseModel):
    """Respuesta para detención de agentes"""

    stopped_agents: List[AgentResponse]


class AgentStopRequest(BaseModel):
    """Solicitud para detener agentes"""

    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    pid: Optional[int] = None
    port: Optional[int] = None

    class Config:
        """Configuración del modelo"""

        json_schema_extra = {
            "example": {"agent_id": "f8c3de3d-1fea-4d7c-a8b0-29f63c4c3454"}
        }


class RuntimeStatusResponse(BaseModel):
    """Respuesta para el endpoint de status del runtime"""

    status: str
    version: str
    app_name: str
    debug_mode: Optional[bool] = None
    active_agents_count: Optional[int] = None
    port: Optional[int] = None
    agent_port_range: Optional[str] = None
    error: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok",
                "version": "0.1.0",
                "app_name": "Generative AI Agent Manager",
                "debug_mode": False,
                "active_agents_count": 3,
                "port": 8000,
                "agent_port_range": "8001-12001",
            }
        }
    }
