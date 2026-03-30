from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..schemas import TokenResponse, LoginRequest, TokenData
from ..utils.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_refresh_token,
)
from ..utils.audit import log_audit
from ..utils.logger import get_logger
from ..utils.odoo_client import get_odoo_client, OdooClient
from ..utils.rate_limiter import limiter
from ..config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticación"])

_REFRESH_COOKIE = "refresh_token"
_COOKIE_MAX_AGE = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86_400  # seconds


def _set_refresh_cookie(response: Response, token: str) -> None:
    """Escribe el refresh token como cookie httpOnly (GAP-02)."""
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        max_age=_COOKIE_MAX_AGE,
        httponly=True,      # No accesible desde JavaScript
        secure=True,        # Solo transmitida por HTTPS
        samesite="strict",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE, httponly=True, secure=True, samesite="strict")


# ---------------------------------------------------------------------------
# Login — rate limit: 5 intentos / minuto por IP (GAP-01)
# ---------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    odoo: OdooClient = Depends(get_odoo_client),
):
    try:
        uid = odoo.common.authenticate(
            settings.ODOO_DB,
            form_data.username,
            form_data.password,
            {},
        )

        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(
            data={"sub": form_data.username, "user_id": uid},
            expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        refresh_token = create_refresh_token(
            data={"sub": form_data.username, "user_id": uid},
        )

        # G2: refresh token en cookie httpOnly — no expuesto en el body
        _set_refresh_cookie(response, refresh_token)

        logger.info("login_success", extra={"username": form_data.username, "uid": uid})
        log_audit(
            action="auth.login",
            user_id=uid,
            resource="session",
            resource_id=None,
            ip=request.client.host if request.client else "-",
            request_id=request.headers.get("X-Request-ID", "-"),
            status="success",
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("login_error", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor",
        )


# ---------------------------------------------------------------------------
# Refresh — rate limit: 10 / minuto; lee refresh token de cookie httpOnly
# (GAP-01, GAP-02)
# ---------------------------------------------------------------------------
@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_token_endpoint(
    request: Request,
    response: Response,
):
    # G2: el refresh token viene en cookie httpOnly, no en el body
    cookie_token = request.cookies.get(_REFRESH_COOKIE)
    if not cookie_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token no encontrado",
        )

    try:
        payload = verify_refresh_token(cookie_token)

        username = payload.get("sub")
        user_id = payload.get("user_id")

        new_access_token = create_access_token(
            data={"sub": username, "user_id": user_id},
            expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        new_refresh_token = create_refresh_token(
            data={"sub": username, "user_id": user_id},
        )

        # Rotar cookie con nuevo refresh token
        _set_refresh_cookie(response, new_refresh_token)

        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("refresh_error", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de actualización inválido",
        )


@router.get("/me", response_model=TokenData)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
):
    return TokenData(
        username=current_user.get("username"),
        user_id=current_user.get("user_id"),
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    _clear_refresh_cookie(response)
    logger.info("logout", extra={"username": current_user.get("username")})
    log_audit(
        action="auth.logout",
        user_id=current_user.get("user_id"),
        resource="session",
        resource_id=None,
        ip=request.client.host if request.client else "-",
        request_id=request.headers.get("X-Request-ID", "-"),
        status="success",
    )
    return {"message": "Logout exitoso"}
