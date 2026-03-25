#!/usr/bin/env python
"""
setup_db.py - Inicialización de PostgreSQL basada en scripts SQL.
Ejecuta, en orden, init de rol/DB, esquema y datos base.
"""
import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from config import load_env_file, BASE_DIR

load_env_file()

DB_NAME = os.getenv("DB_NAME", "talentflow_db")
DB_USER = os.getenv("DB_USER", "talentflow_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "talentflow123")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
if DB_HOST.strip().lower() in ("localhost", "::1"):
    DB_HOST = "127.0.0.1"
DB_PORT = os.getenv("DB_PORT", "5432")

# Credenciales administrativas para ejecutar creación de rol/DB.
DB_ADMIN_USER = os.getenv("DB_ADMIN_USER", "postgres")
DB_ADMIN_PASSWORD = os.getenv("DB_ADMIN_PASSWORD", "")
DB_ADMIN_DB = os.getenv("DB_ADMIN_DB", "postgres")

DB_SCRIPTS_DIR = BASE_DIR / "database"


def _read_sql_text(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _render_sql_template(path: Path) -> str:
    content = _read_sql_text(path)
    replacements = {
        "__DB_NAME__": DB_NAME,
        "__DB_USER__": DB_USER,
        "__DB_PASSWORD__": DB_PASSWORD,
    }
    for key, value in replacements.items():
        content = content.replace(key, value)
    return content


def _run_sql_script(sql_path: Path, dbname: str, user: str, password: str, autocommit: bool = False):
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=DB_HOST,
            port=DB_PORT,
        )
        # Evita UnicodeDecodeError con mensajes del servidor en Windows (p. ej. LATIN1/WIN1252).
        try:
            conn.set_client_encoding("WIN1252")
        except Exception:
            pass
        if autocommit:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cursor:
            cursor.execute(_render_sql_template(sql_path))
        if not autocommit:
            conn.commit()
        print(f"[OK] Script ejecutado: {sql_path.name}")
    except Exception as exc:
        print(f"[ERROR] Falló {sql_path.name}: {exc}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


def _sync_app_role_password():
    """Alinea la contraseña del rol de la app con DB_PASSWORD en .env.

    00_init_role_db.sql solo crea el rol si no existe; si ya existía con otra
    clave, la app falla con «password authentication failed». ALTER ROLE evita eso.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_ADMIN_DB,
            user=DB_ADMIN_USER,
            password=DB_ADMIN_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        try:
            conn.set_client_encoding("WIN1252")
        except Exception:
            pass
        with conn.cursor() as cursor:
            cursor.execute(
                sql.SQL("ALTER ROLE {} PASSWORD {}").format(
                    sql.Identifier(DB_USER),
                    sql.Literal(DB_PASSWORD),
                )
            )
        print(f"[OK] Contraseña del rol '{DB_USER}' sincronizada con .env (ALTER ROLE).")
    except Exception as exc:
        print(f"[ERROR] No se pudo sincronizar contraseña del rol: {exc}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


def _ensure_database_exists():
    """CREATE DATABASE no puede ir dentro de un bloque DO/transacción; se hace aparte."""
    conn = psycopg2.connect(
        dbname=DB_ADMIN_DB,
        user=DB_ADMIN_USER,
        password=DB_ADMIN_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    try:
        try:
            conn.set_client_encoding("WIN1252")
        except Exception:
            pass
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (DB_NAME,),
            )
            if cursor.fetchone():
                return
            cursor.execute(
                sql.SQL("CREATE DATABASE {} OWNER {}").format(
                    sql.Identifier(DB_NAME),
                    sql.Identifier(DB_USER),
                )
            )
            print(f"[OK] Base de datos '{DB_NAME}' creada.")
    finally:
        conn.close()


def main():
    required_scripts = [
        DB_SCRIPTS_DIR / "00_init_role_db.sql",
        DB_SCRIPTS_DIR / "01_schema.sql",
        DB_SCRIPTS_DIR / "02_seed.sql",
    ]
    missing = [str(script) for script in required_scripts if not script.exists()]
    if missing:
        print("[ERROR] Faltan scripts SQL requeridos:")
        for file_path in missing:
            print(f"  - {file_path}")
        sys.exit(1)

    print("==> Inicializando rol y base de datos...")
    _run_sql_script(
        required_scripts[0],
        dbname=DB_ADMIN_DB,
        user=DB_ADMIN_USER,
        password=DB_ADMIN_PASSWORD,
        autocommit=True,
    )
    _sync_app_role_password()
    _ensure_database_exists()

    print("==> Aplicando esquema...")
    _run_sql_script(
        required_scripts[1],
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    print("==> Insertando datos base...")
    _run_sql_script(
        required_scripts[2],
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

    print("Inicialización de base de datos completada correctamente.")


if __name__ == "__main__":
    main()