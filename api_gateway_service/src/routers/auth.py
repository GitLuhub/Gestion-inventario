from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from ..schemas import TokenResponse, LoginRequest, TokenData
from ..utils.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_refresh_token,
)
from ..utils.odoo_client import get_odoo_client, OdooClient
from ..config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    odoo: OdooClient = Depends(get_odoo_client)
):
    try:
        uid = odoo.common.authenticate(
            settings.ODOO_DB,
            form_data.username,
            form_data.password,
            {}
        )
        
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(
            data={
                "sub": form_data.username,
                "user_id": uid,
            },
            expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = create_refresh_token(
            data={
                "sub": form_data.username,
                "user_id": uid,
            }
        )
        
        logger.info(f"Login exitoso para usuario: {form_data.username}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=refresh_token,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    try:
        payload = verify_refresh_token(refresh_token)
        
        username = payload.get("sub")
        user_id = payload.get("user_id")
        
        new_access_token = create_access_token(
            data={"sub": username, "user_id": user_id},
            expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        new_refresh_token = create_refresh_token(
            data={"sub": username, "user_id": user_id}
        )
        
        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_token=new_refresh_token,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de actualización inválido",
        )


@router.get("/me", response_model=TokenData)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    return TokenData(
        username=current_user.get("username"),
        user_id=current_user.get("user_id"),
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    logger.info(f"Logout para usuario: {current_user.get('username')}")
    return {"message": "Logout exitoso"}
