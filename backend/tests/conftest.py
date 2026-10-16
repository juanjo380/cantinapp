"""Variables de entorno para poder importar `app.core.config` en los tests sin
una base de datos real."""
import os

os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("JWT_SECRET", "test-secret")
