from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuracion cargada desde variables de entorno / archivo .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CantinAPP API"
    environment: str = "development"

    # Conexion a Supabase (PostgreSQL). Se separan los campos para evitar
    # problemas de codificacion si el password tiene caracteres especiales.
    db_host: str
    db_port: int = 5432
    db_name: str = "postgres"
    db_user: str
    db_password: SecretStr

    db_ssl: bool = True
    db_use_transaction_pooler: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 5
    db_echo: bool = False

    # JWT (RF-02). En produccion define JWT_SECRET por variable de entorno.
    jwt_secret: str = "dev-secret-change-me"  # shortcut: default de desarrollo, cambiar en prod
    jwt_expire_minutes: int = 720

    # Reglas de negocio (doc 1 / RNF-04)
    min_history_days: int = 30
    default_forecast_days: int = 30

    cors_origins: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()