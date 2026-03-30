"""
Logging estructurado en JSON para ETL Service.

Emite cada log record como una línea JSON a stdout (recogida por Promtail/Loki)
y opcionalmente a un archivo rotativo diario.

Uso:
    from utils.logger_util import get_logger
    logger = get_logger('etl.extract')
    logger.info('records_extracted', extra={'count': 42, 'source': 'csv'})
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from config import Config
except ImportError:
    class Config:  # type: ignore[no-redef]
        LOG_LEVEL = 'INFO'
        LOG_DIR = '/app/logs'


_SKIP_FIELDS = frozenset({
    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
    'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
    'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
    'processName', 'process', 'message', 'taskName',
})


class _JsonFormatter(logging.Formatter):
    """Serializa cada LogRecord como una línea JSON."""

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        obj: dict = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.message,
            'service': 'etl',
        }
        if record.exc_info:
            obj['exception'] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in _SKIP_FIELDS:
                obj[key] = value
        return json.dumps(obj, ensure_ascii=False, default=str)


def _build_logger(name: str, log_level: str, log_dir: str) -> logging.Logger:
    lgr = logging.getLogger(name)
    lgr.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    if lgr.handlers:
        return lgr

    fmt = _JsonFormatter()

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    lgr.addHandler(ch)

    try:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(
            log_path / f'etl_{datetime.now().strftime("%Y%m%d")}.log'
        )
        fh.setFormatter(fmt)
        lgr.addHandler(fh)
    except OSError:
        pass  # Log directory not writable — stdout only

    lgr.propagate = False
    return lgr


_loggers: dict = {}


def get_logger(name: str = 'ETL') -> logging.Logger:
    """Retorna un logger JSON singleton por nombre."""
    if name not in _loggers:
        _loggers[name] = _build_logger(name, Config.LOG_LEVEL, Config.LOG_DIR)
    return _loggers[name]
