"""
TalentFlow — Carga de variables de entorno y configuración tipada.

El archivo .env debe estar en UTF-8 (recomendado en Windows para evitar
caracteres corruptos en contraseñas o correos).
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent


def load_env_file() -> None:
    """Carga .env desde la raíz del proyecto o desde DOTENV_PATH si está definido."""
    custom = os.environ.get("DOTENV_PATH")
    env_path = Path(custom).resolve() if custom else BASE_DIR / ".env"
    if env_path.is_file():
        load_dotenv(env_path, encoding="utf-8")
    else:
        # No fallar: la app puede depender solo de variables del sistema
        load_dotenv(encoding="utf-8")


def env_bool(key: str, default: bool = False) -> bool:
    v = os.getenv(key)
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def env_int(key: str, default: int) -> int:
    try:
        return int(str(os.getenv(key, str(default))).strip())
    except ValueError:
        return default


def log_config_warnings(logger: logging.Logger | None = None) -> None:
    """Advertencias de configuración al arrancar (no bloquea el arranque)."""
    log = logger or logging.getLogger("talentflow.config")
    if not os.getenv("SECRET_KEY") or os.getenv("SECRET_KEY") == "dev-key-insegura":
        if os.getenv("FLASK_ENV") == "production":
            log.warning(
                "SECRET_KEY es insegura o por defecto y FLASK_ENV=production. "
                "Define una clave aleatoria larga en .env."
            )
    if not (os.getenv("DB_USER") and os.getenv("DB_NAME")):
        log.warning("DB_USER o DB_NAME no definidos en entorno; se usarán valores por defecto.")
    if not os.getenv("MAIL_USERNAME"):
        log.info("MAIL_USERNAME vacío: los correos automáticos estarán desactivados.")


def get_mail_config() -> dict:
    return {
        "MAIL_SERVER": os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        "MAIL_PORT": env_int("MAIL_PORT", 587),
        "MAIL_USE_TLS": env_bool("MAIL_USE_TLS", True),
        "MAIL_USERNAME": os.getenv("MAIL_USERNAME", ""),
        "MAIL_PASSWORD": os.getenv("MAIL_PASSWORD", ""),
    }


def get_flask_run_config() -> dict:
    """host: 127.0.0.1 solo local; 0.0.0.0 permite acceso desde otros equipos en la LAN."""
    host = (os.getenv("FLASK_RUN_HOST") or "127.0.0.1").strip()
    return {
        "debug": env_bool("FLASK_DEBUG", True),
        "host": host,
        "port": env_int("FLASK_RUN_PORT", 5000),
    }
