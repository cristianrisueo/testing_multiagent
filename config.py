import os
from pydantic_settings import BaseSettings
from pathlib import Path
import logging
import sys

# Obtiene el directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Configuración centralizada de la aplicación utilizando Pydantic BaseSettings.

    Esta clase gestiona todos los parámetros configurables del sistema, incluyendo:
    - Configuración general (nombre de la aplicación, modo debug)
    - Rangos de puertos para la API principal y los servicios de agentes
    - Rutas de archivos y directorios para datos persistentes
    - Timeouts y otros parámetros operativos

    Los valores se cargan con el siguiente orden de prioridad:
    1. Variables de entorno
    2. Archivo .env
    3. Valores predeterminados definidos en la clase
    """

    # Configuración general
    APP_NAME: str = "Generative AI Agent Manager"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    VERSION: str = "0.1.0"

    # Configuración de puertos. 8000 para el servicio principal
    PORT: int = int(os.getenv("PORT", "8000"))
    MIN_AGENT_PORT: int = 8001
    MAX_AGENT_PORT: int = 12001

    # Directorios y archivos
    AGENTS_DIR: Path = BASE_DIR / "agents"
    LOG_DIR: Path = BASE_DIR / "logs"

    # Configuración de agentes (iniciar y cerrar)
    AGENT_STARTUP_TIMEOUT: int = 30
    AGENT_SHUTDOWN_TIMEOUT: int = 30

    # Configuración de logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FORMAT: str = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    # Clase añadida que configura el comportamiento de Pydantic para env
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()  # Instancia la configuración

# Configurar el logger principal
app_logger = logging.getLogger("app")
app_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

# Eliminar handlers existentes si los hay
while app_logger.handlers:
    app_logger.handlers.pop()

# Formato común para todos los logs
log_formatter = logging.Formatter(
    fmt=settings.LOG_FORMAT, datefmt=settings.LOG_DATE_FORMAT
)

# Handler para consola
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setFormatter(log_formatter)
app_logger.addHandler(console_handler)

# Para asegurar que los loggers de uvicorn y fastapi usen la misma configuración
for logger_name in ["uvicorn", "uvicorn.access", "fastapi"]:
    logger = logging.getLogger(logger_name)
    logger.handlers = []
    logger.propagate = False
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    logger.addHandler(console_handler)
