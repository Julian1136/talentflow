"""
TalentFlow — Plataforma de Gestión de Selección de Candidatos
Punto de entrada principal de la aplicación Flask
"""

import os
import sys

# Ayuda a alinear codificación cliente/servidor cuando se usa psycopg2 (no Windows).
if sys.platform != "win32":
    os.environ.setdefault("PGCLIENTENCODING", "UTF8")

from config import (
    load_env_file,
    log_config_warnings,
    get_mail_config,
    get_flask_run_config,
    env_int,
    env_bool,
)
from flask import Flask
from sqlalchemy.engine.url import URL
from extensions import db, login_manager

load_env_file()


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ── Configuración ──────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-key-insegura")
    db_user = os.getenv("DB_USER", "talentflow_user")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    if db_host.strip().lower() in ("localhost", "::1"):
        db_host = "127.0.0.1"
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "talentflow_db")
    try:
        db_port_int = int(str(db_port).strip())
    except ValueError:
        db_port_int = 5432

    # En Windows, psycopg2 (libpq) puede lanzar UnicodeDecodeError al fallar la conexión
    # si el mensaje de error va en CP1252. psycopg 3 no tiene ese problema.
    if sys.platform == "win32":
        _pg_driver = "postgresql+psycopg"
        _engine_opts = {}
    else:
        _pg_driver = "postgresql+psycopg2"
        _engine_opts = {"connect_args": {"client_encoding": "UTF8"}}

    app.config["SQLALCHEMY_DATABASE_URI"] = URL.create(
        drivername=_pg_driver,
        username=db_user,
        password=db_password,
        host=db_host,
        port=db_port_int,
        database=db_name,
    )
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = _engine_opts
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    upload_folder = os.getenv("UPLOAD_FOLDER", "uploads/candidatos")
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, upload_folder)
    app.config["MAX_CONTENT_LENGTH"] = env_int("MAX_CONTENT_LENGTH_MB", 10) * 1024 * 1024
    if os.path.exists(app.config["UPLOAD_FOLDER"]) and not os.path.isdir(app.config["UPLOAD_FOLDER"]):
        app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads", "candidatos_files")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Email (Flask-Mail) ─────────────────────────────────────────
    app.config.update(get_mail_config())

    # ── Extensiones ────────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Inicia sesión para acceder a TalentFlow."
    login_manager.login_message_category = "warning"

    from services.email_service import init_mail

    init_mail(app)

    # ── Blueprints (módulos) ───────────────────────────────────────
    from controllers.auth_controller import auth_bp
    from controllers.candidato_controller import candidatos_bp
    from controllers.vacante_controller import vacantes_bp
    from controllers.proceso_controller import proceso_bp
    from controllers.dashboard_controller import dashboard_bp, reportes_bp
    from controllers.kanban_controller import kanban_bp
    from controllers.calendario_controller import calendario_bp
    from controllers.firma_controller import firma_bp
    from controllers.publico_controller import publico_bp
    from controllers.empleado_controller import empleados_bp
    from controllers.config_controller import config_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(candidatos_bp)
    app.register_blueprint(vacantes_bp)
    app.register_blueprint(proceso_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(kanban_bp)
    app.register_blueprint(calendario_bp)
    app.register_blueprint(firma_bp)
    app.register_blueprint(publico_bp)
    app.register_blueprint(empleados_bp)
    app.register_blueprint(config_bp)

    # ── User loader para Flask-Login ───────────────────────────────
    from models import ConfiguracionTema, Usuario

    @login_manager.user_loader  
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    @app.context_processor
    def inject_theme():
        try:
            cfg = db.session.get(ConfiguracionTema, 1)
            if not cfg:
                return {}
            return {"theme_cfg": cfg}
        except Exception:
            # Permite arrancar aunque aún no se aplique 06_hr_lifecycle.sql
            return {}

    log_config_warnings(app.logger)

    _maybe_start_scheduler(app)

    return app


def _maybe_start_scheduler(app):
    """APScheduler opcional (recordatorios / tareas en background)."""
    if not env_bool("ENABLE_SCHEDULER", False):
        return
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from services.scheduler_jobs import register_scheduler_jobs

        scheduler = BackgroundScheduler(daemon=True)
        register_scheduler_jobs(scheduler, app)
        scheduler.start()
        app.scheduler = scheduler
        app.logger.info("APScheduler iniciado (ENABLE_SCHEDULER=True).")
    except Exception as exc:
        app.logger.warning("No se pudo iniciar APScheduler: %s", exc)


app = create_app()

if __name__ == "__main__":
    run_cfg = get_flask_run_config()
    app.run(
        debug=run_cfg["debug"],
        host=run_cfg["host"],
        port=run_cfg["port"],
    )
