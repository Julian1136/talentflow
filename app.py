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
from flask_login import current_user
from sqlalchemy.engine.url import URL
from extensions import db, login_manager, csrf, limiter

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
    csrf.init_app(app)
    limiter.init_app(app)
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

    @app.context_processor
    def inject_quick_notifications():
        if not current_user.is_authenticated:
            return {}
        try:
            from models import Aplicacion, Entrevista, EvaluacionDesempeno
            from datetime import datetime, timedelta

            now = datetime.utcnow()
            soon = now + timedelta(hours=48)
            entrevistas = (
                Entrevista.query.join(Aplicacion, Aplicacion.id == Entrevista.id_aplicacion)
                .filter(
                    Entrevista.resultado == "pendiente",
                    Entrevista.fecha_programada.isnot(None),
                    Entrevista.fecha_programada >= now,
                    Entrevista.fecha_programada <= soon,
                )
                .order_by(Entrevista.fecha_programada.asc())
                .limit(6)
                .all()
            )
            evals_pend = (
                EvaluacionDesempeno.query.filter_by(estado_aceptacion="pendiente_empleado")
                .order_by(EvaluacionDesempeno.fecha_registro.desc())
                .limit(6)
                .all()
            )

            items = []
            for e in entrevistas:
                candidato = e.aplicacion.candidato.nombre_completo if e.aplicacion and e.aplicacion.candidato else "Candidato"
                fecha = e.fecha_programada.strftime("%d/%m %H:%M") if e.fecha_programada else "—"
                notif_key = f"entrevista:{e.id}"
                items.append(
                    {
                        "key": notif_key,
                        "tipo": "entrevista",
                        "texto": f"Entrevista próxima: {candidato} ({fecha})",
                        "url": url_for("proceso.detalle", app_id=e.id_aplicacion),
                    }
                )
            for ev in evals_pend:
                nombre = ev.empleado.candidato.nombre_completo if ev.empleado and ev.empleado.candidato else ev.id_empleado
                notif_key = f"evaluacion:{ev.id}"
                items.append(
                    {
                        "key": notif_key,
                        "tipo": "desempeno",
                        "texto": f"Evaluación pendiente de aceptación: {nombre}",
                        "url": url_for("empleados.detalle", emp_id=ev.id_empleado),
                    }
                )
            try:
                from services.notifications_store import was_seen

                items = [x for x in items if not was_seen(current_user.id, x.get("key", ""))]
            except Exception:
                pass
            try:
                from services.sla_notifications import collect_sla_notification_items
                from services.notifications_store import was_seen as _was_seen_sla

                for s in collect_sla_notification_items(limit=8):
                    if not _was_seen_sla(current_user.id, s.get("key", "")):
                        items.append(s)
            except Exception:
                pass

            items = items[:14]
            by_type = {"entrevista": 0, "desempeno": 0, "sla": 0}
            for it in items:
                t = it.get("tipo")
                if t in by_type:
                    by_type[t] += 1
            return {
                "quick_notifications": items,
                "quick_notifications_count": len(items),
                "quick_notifications_by_type": by_type,
            }
        except Exception:
            return {
                "quick_notifications": [],
                "quick_notifications_count": 0,
                "quick_notifications_by_type": {"entrevista": 0, "desempeno": 0, "sla": 0},
            }

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
