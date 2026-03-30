"""
RequestIDMiddleware — correlación de logs por petición.

Asigna un UUID único a cada request HTTP:
  - Lee X-Request-ID del cliente si viene (útil para trazabilidad end-to-end).
  - Genera uno nuevo si no viene.
  - Lo almacena en la ContextVar `request_id_var` para que todos los loggers
    de la misma tarea async lo incluyan automáticamente.
  - Lo devuelve en la cabecera X-Request-ID de la respuesta.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..utils.logger import request_id_var


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inyecta request_id en contexto y en cabecera de respuesta."""

    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        token = request_id_var.set(req_id)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers['X-Request-ID'] = req_id
        return response
