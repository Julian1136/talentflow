"""
Ítems de SLA / alertas operativas para la campana de notificaciones (Fase 2–3).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func

from extensions import db
from models import Aplicacion, HistorialProceso, Vacante


def collect_sla_notification_items(limit: int = 6) -> list[dict]:
    items: list[dict] = []
    now = datetime.utcnow()
    stale_days = 10
    limite = now - timedelta(days=stale_days)

    sub_last = (
        db.session.query(
            HistorialProceso.id_aplicacion.label("aid"),
            func.max(HistorialProceso.fecha_accion).label("last_dt"),
        )
        .filter(HistorialProceso.id_aplicacion.isnot(None))
        .group_by(HistorialProceso.id_aplicacion)
        .subquery()
    )

    stale_apps = (
        db.session.query(Aplicacion)
        .outerjoin(sub_last, sub_last.c.aid == Aplicacion.id)
        .filter(
            Aplicacion.estado.notin_(["contratado", "rechazado"]),
            db.or_(sub_last.c.last_dt.is_(None), sub_last.c.last_dt < limite),
        )
        .order_by(Aplicacion.fecha_aplicacion.asc())
        .limit(limit)
        .all()
    )
    for ap in stale_apps:
        nom = ap.candidato.nombre_completo if ap.candidato else ap.cedula_candidato
        items.append(
            {
                "key": f"sla:stale_app:{ap.id}",
                "tipo": "sla",
                "texto": f"Sin movimiento (+{stale_days} d): {nom} · {ap.vacante.titulo if ap.vacante else ''}",
                "url": f"/proceso/{ap.id}",
            }
        )

    vac_sin = (
        Vacante.query.filter(
            Vacante.estado == "abierta",
            Vacante.fecha_creacion < now - timedelta(days=14),
        )
        .order_by(Vacante.fecha_creacion.asc())
        .limit(5)
        .all()
    )
    for v in vac_sin:
        n = Aplicacion.query.filter_by(id_vacante=v.id).count()
        if n == 0:
            items.append(
                {
                    "key": f"sla:vac_empty:{v.id}",
                    "tipo": "sla",
                    "texto": f"Vacante abierta sin postulaciones (+14 d): {v.titulo}",
                    "url": f"/vacantes/{v.id}",
                }
            )

    return items[:limit]
