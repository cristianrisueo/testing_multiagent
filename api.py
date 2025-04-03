from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict
from .config import app_logger as logger, settings
from .models import (
    ManifestPayload,
    AgentListResponse,
    AgentLaunchResponse,
    AgentStopResponse,
    AgentStopRequest,
    AgentException,
    AgentResponse,
    agent_exception_handler,
    RuntimeStatusResponse,
)
from .services import agent_manager


router = APIRouter()  # Router del API


@router.post("/launch_agents", response_model=AgentLaunchResponse)
async def launch_agents(payload: ManifestPayload) -> Dict[str, list[AgentResponse]]:
    """
    Lanza agentes basados en el manifest

    - Verifica si los agentes solicitados están disponibles
    - Inicia un nuevo servicio para cada agente disponible
    - Devuelve información sobre los agentes lanzados
    """

    try:
        logger.info("Solicitando lanzamiento de agentes: %s", payload.agents)

        launched_agents = await agent_manager.launch_agents(
            payload.agents, payload.resources
        )

        logger.info(
            "Agentes lanzados exitosamente: %s", [a.name for a in launched_agents]
        )

        return {"launched_agents": launched_agents}
    except AgentException as exc:
        logger.error("Error al lanzar agentes: %s", exc)
        raise agent_exception_handler(exc)


@router.post("/stop_agent", response_model=AgentStopResponse)
async def stop_agent(
    request: Optional[AgentStopRequest] = None,
    agent_id: Optional[str] = Query(None),
    agent_name: Optional[str] = Query(None),
    pid: Optional[int] = Query(None),
    port: Optional[int] = Query(None),
) -> Dict[str, list[AgentResponse]]:
    """
    Detiene agentes según los criterios proporcionados

    - Permite detener agentes usando diferentes identificadores
    - Intenta un cierre controlado
    - Devuelve información sobre los agentes detenidos
    """

    # Combina parámetros de query y body. Permite usar ambos
    # y usa el que encuentre empezando por el body
    if request:
        agent_id = request.agent_id or agent_id
        agent_name = request.agent_name or agent_name
        pid = request.pid or pid
        port = request.port or port

    # Registrar la solicitud de detención
    criteria = ", ".join(
        filter(
            None,
            [
                f"agent_id={agent_id}" if agent_id else None,
                f"agent_name={agent_name}" if agent_name else None,
                f"pid={pid}" if pid else None,
                f"port={port}" if port else None,
            ],
        )
    )
    logger.info("Solicitando detención de agente(s) con criterios: %s", criteria)

    # Detiene los agentes y devuelve una lista con los agentes detenidos
    # o una excepción de error. Aclaración: Agente == Micro
    try:
        stopped_agents = await agent_manager.stop_agent(
            agent_id=agent_id, agent_name=agent_name, pid=pid, port=port
        )

        logger.info(
            "Agentes detenidos exitosamente: %s", [a.name for a in stopped_agents]
        )

        return {"stopped_agents": stopped_agents}
    except AgentException as exc:
        logger.error("Error al detener agente(s): %s", exc)
        raise agent_exception_handler(exc)


@router.post("/stop_agents", response_model=AgentStopResponse)
async def stop_agents() -> Dict[str, list[AgentResponse]]:
    """
    Detiene todos los agentes en ejecución

    - Intenta un cierre controlado de todos los agentes activos
    - Devuelve información sobre los agentes detenidos
    """
    logger.info("Solicitando detención de todos los agentes")

    try:
        stopped_agents = await agent_manager.stop_all_agents()

        logger.info(
            "Todos los agentes detenidos exitosamente: %s",
            [a.name for a in stopped_agents],
        )

        return {"stopped_agents": stopped_agents}
    except Exception as exc:
        logger.error("Error al detener todos los agentes: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/list_agents", response_model=AgentListResponse)
async def list_agents(
    status: Optional[str] = Query(
        None,
        description="Filtrar por estado (running, starting, stopping, stopped, error)",
    ),
    agent_name: Optional[str] = Query(None, description="Filtrar por nombre de agente"),
) -> Dict[str, list[AgentResponse]]:
    """
    Lista agentes con filtros opcionales

    - Permite filtrar por estado o nombre
    - Devuelve información completa sobre los agentes
    """

    # Registra la solicitud de listado
    filters = ", ".join(
        filter(
            None,
            [
                f"status={status}" if status else None,
                f"agent_name={agent_name}" if agent_name else None,
            ],
        )
    )
    logger.debug("Solicitando listado de agentes con filtros: %s", filters or "ninguno")

    # Busca al agente por nombre o estado
    try:
        agents = agent_manager.list_agents(status=status, agent_name=agent_name)

        logger.debug(
            "Se encontraron %s agentes que coinciden con los filtros", len(agents)
        )

        return {"agents": agents}
    except Exception as e:
        logger.error("Error al listar agentes: %s", str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=RuntimeStatusResponse)
async def status() -> Dict[str, any]:
    """
    Comprueba el estado del runtime

    - Devuelve información básica sobre el estado del runtime
    - Incluye versión, configuración y cantidad de agentes activos
    """
    logger.debug("Solicitando estado del runtime")

    try:
        # Obtener la lista de agentes activos
        active_agents = agent_manager.list_agents()

        # Crear respuesta con información del runtime
        response = {
            "status": "ok",
            "version": settings.VERSION,
            "app_name": settings.APP_NAME,
            "debug_mode": settings.DEBUG,
            "active_agents_count": len(active_agents),
            "port": settings.PORT,
            "agent_port_range": f"{settings.MIN_AGENT_PORT}-{settings.MAX_AGENT_PORT}",
        }

        logger.debug("Estado del runtime obtenido correctamente")
        return response
    except Exception as e:
        logger.error("Error al obtener estado del runtime: %s", str(e))
        return {
            "status": "error",
            "error": str(e),
            "version": settings.VERSION,
            "app_name": settings.APP_NAME,
        }
