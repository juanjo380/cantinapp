from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_JWT_SECRET = "dev-secret-change-me"


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
    jwt_secret: str = _DEV_JWT_SECRET
    jwt_expire_minutes: int = 720

    # Reglas de negocio (doc 1 / RNF-04)
    min_history_days: int = 30
    default_forecast_days: int = 30

    # Co-ocurrencia temporal de picos (recomendaciones Fase 1)
    cooccurrence_window_days: int = 14
    cooccurrence_sigma: float = 2.0
    cooccurrence_max_lag_days: int = 3
    cooccurrence_min_hits: int = 3

    cors_origins: list[str] = ["*"]

    @model_validator(mode="after")
    def _require_real_secret_outside_dev(self) -> "Settings":
        # Con el secreto por defecto cualquiera puede firmar tokens de cualquier usuario.
        if self.environment != "development" and (
            self.jwt_secret == _DEV_JWT_SECRET or len(self.jwt_secret) < 32
        ):
            raise ValueError("JWT_SECRET debe definirse (mínimo 32 caracteres) fuera de development")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()