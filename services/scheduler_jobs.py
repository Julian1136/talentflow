"""
Jobs de APScheduler (opcional). Active con ENABLE_SCHEDULER=True en .env.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func


def _minutos_backoff(intentos: int) -> int:
    return min(180, 5 * (2 ** max(0, intentos)))


def register_scheduler_jobs(scheduler, app):
    """Registra tareas en el scheduler; se ejecuta dentro de create_app."""

    def recordatorios_entrevista_24h():
        with app.app_context():
            from extensions import db
            from models import Entrevista
            from services.email_service import notificar_recordatorio_entrevista_24h

            now = datetime.utcnow()
            ventana_ini = now + timedelta(hours=23)
            ventana_fin = now + timedelta(hours=25)
            q = Entrevista.query.filter(
                Entrevista.resultado == "pendiente",
                Entrevista.fecha_programada.isnot(None),
                Entrevista.fecha_programada >= ventana_ini,
                Entrevista.fecha_programada <= ventana_fin,
                Entrevista.recordatorio_enviado_en.is_(None),
            )
            for ent in q.limit(50).all():
                try:
                    ok = notificar_recordatorio_entrevista_24h(ent)
                    if ok:
                        ent.recordatorio_enviado_en = datetime.utcnow()
                        db.session.add(ent)
                except Exception as exc:
                    app.logger.warning("Recordatorio entrevista %s: %s", ent.id, exc)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

    def reintentar_cola_correo():
        with app.app_context():
            from extensions import db
            from models import CorreoColaReintento
            from services.email_service import reenviar_desde_cola

            now = datetime.utcnow()
            q = (
                CorreoColaReintento.query.filter(
                    CorreoColaReintento.enviado_en.is_(None),
                    CorreoColaReintento.intentos
                    < func.coalesce(CorreoColaReintento.max_intentos, 5),
                    db.or_(
                        CorreoColaReintento.proximo_intento_en.is_(None),
                        CorreoColaReintento.proximo_intento_en <= now,
                    ),
                )
                .order_by(CorreoColaReintento.creado_en.asc())
                .limit(25)
            )
            for row in q.all():
                try:
                    max_i = row.max_intentos if row.max_intentos is not None else 5
                    ok = reenviar_desde_cola(row)
                    if ok:
                        row.enviado_en = datetime.utcnow()
                        row.ultimo_error = None
                    else:
                        row.intentos = (row.intentos or 0) + 1
                        if row.intentos >= max_i:
                            row.ultimo_error = (row.ultimo_error or "")[:1500] + " | max intentos"
                        else:
                            row.proximo_intento_en = now + timedelta(minutes=_minutos_backoff(row.intentos))
                    db.session.add(row)
                except Exception as exc:
                    app.logger.warning("Reintento correo id=%s: %s", row.id, exc)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()

    scheduler.add_job(
        recordatorios_entrevista_24h,
        "interval",
        hours=1,
        id="tf_recordatorio_entrevista_24h",
        replace_existing=True,
    )
    scheduler.add_job(
        reintentar_cola_correo,
        "interval",
        minutes=10,
        id="tf_reintento_cola_correo",
        replace_existing=True,
    )
