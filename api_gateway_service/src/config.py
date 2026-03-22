from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'
    )
    
    APP_NAME: str = "API Gateway - Gestión de Inventario"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    ODOO_URL: str = "http://odoo_app:8069"
    ODOO_DB: str = "odoo_db"
    ODOO_USER: str = "admin"
    ODOO_PASSWORD: str = "admin"
    
    JWT_SECRET_KEY: str = "supersecretkey-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    
    @property
    def cors_origins_list(self) -> list:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
    
    @property
    def odoo_password_from_file(self) -> str:
        password_file = os.getenv('ODOO_PASSWORD_FILE', '')
        if password_file and os.path.exists(password_file):
            with open(password_file, 'r') as f:
                return f.read().strip()
        return self.ODOO_PASSWORD
    
    @property
    def jwt_secret_from_file(self) -> str:
        secret_file = os.getenv('JWT_SECRET_KEY_FILE', '')
        if secret_file and os.path.exists(secret_file):
            with open(secret_file, 'r') as f:
                return f.read().strip()
        return self.JWT_SECRET_KEY


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
