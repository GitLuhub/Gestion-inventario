"""
Logging estructurado en JSON para API Gateway.

Cada log record se emite como una línea JSON con:
  - timestamp (ISO-8601 UTC)
  - level, logger, message
  - request_id  — propagado vía ContextVar desde RequestIDMiddleware
  - Cualquier campo extra pasado con extra={...}

Uso:
    from src.utils.logger import get_logger, setup_json_logging
    setup_json_logging(settings.LOG_LEVEL)
    logger = get_logger(__name__)
    logger.info("evento", extra={"user_id": 42})
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Context variable — el middleware asigna el request_id aquí; todos los
# loggers lo leen automáticamente sin necesitar parámetros explícitos.
# ---------------------------------------------------------------------------
request_id_var: ContextVar[str] = ContextVar('request_id', default='-')

_SKIP_FIELDS = frozenset({
    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
    'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
    'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
    'processName', 'process', 'message', 'taskName',
})


class JsonFormatter(logging.Formatter):
    """Serializa cada LogRecord como una línea JSON."""

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        log_obj: dict = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.message,
            'request_id': request_id_var.get(),
        }
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in _SKIP_FIELDS:
                log_obj[key] = value
        return json.dumps(log_obj, ensure_ascii=False, default=str)


def setup_json_logging(log_level: str = 'INFO') -> None:
    """
    Reemplaza la configuración de logging del proceso con un handler JSON en stdout.
    Llamar una sola vez al inicio de la aplicación (lifespan).
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root.handlers.clear()
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
