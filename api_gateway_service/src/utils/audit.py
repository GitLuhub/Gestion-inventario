"""
audit.py — AuditLog formal para el API Gateway (J4 / GAP-17)

Registra un evento de auditoría estructurado cada vez que ocurre una acción
importante: login, logout, creación/modificación de recursos, ajustes de stock.

El evento se emite como un log JSON con el campo "audit": true, lo que permite
a Loki/Grafana filtrarlo separadamente del tráfico operacional ordinario.

Uso:
    from src.utils.audit import log_audit

    @router.post("/products")
    async def create_product(request: Request, ...):
        ...
        log_audit(
            action="product.create",
            user_id=current_user["user_id"],
            resource="product",
            resource_id=str(new_id),
            ip=request.client.host,
            request_id=request.headers.get("X-Request-ID", "-"),
            status="success",
            details={"name": product_data.name},
        )
"""

from typing import Any
from .logger import get_logger

_audit_logger = get_logger("audit")


def log_audit(
    action: str,
    user_id: int | None,
    resource: str,
    resource_id: str | None,
    ip: str,
    request_id: str,
    status: str,
    details: dict[str, Any] | None = None,
) -> None:
    """
    Emite un evento de auditoría como log JSON estructurado.

    Parámetros:
        action      : Nombre del evento — ej. "auth.login", "product.create"
        user_id     : ID del usuario que realizó la acción (None si anónimo)
        resource    : Tipo de recurso afectado — ej. "product", "adjustment"
        resource_id : ID del recurso afectado (None si no aplica)
        ip          : Dirección IP del cliente
        request_id  : UUID de la petición HTTP (X-Request-ID)
        status      : "success" | "failure" | "blocked"
        details     : Contexto adicional (evitar datos sensibles: contraseñas, tokens)
    """
    _audit_logger.info(
        "audit_event",
        extra={
            "audit": True,           # etiqueta para filtrar en Loki
            "action": action,
            "user_id": user_id,
            "resource": resource,
            "resource_id": resource_id,
            "ip": ip,
            "request_id": request_id,
            "status": status,
            "details": details or {},
        },
    )
