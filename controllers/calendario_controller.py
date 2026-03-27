"""
TalentFlow — Calendario de entrevistas (FullCalendar)
"""

from datetime import datetime, date

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func as sa_func
from sqlalchemy.orm import joinedload

from extensions import db
from models import Aplicacion, Entrevista, HistorialProceso, Usuario


calendario_bp = Blueprint("calendario", __name__, url_prefix="/calendario")


def _registrar_historial(aplicacion, accion, estado_ant=None, estado_nuevo=None, obs=None):
    h = HistorialProceso(
        cedula_candidato=aplicacion.cedula_candidato,
        id_aplicacion=aplicacion.id,
        id_usuario=current_user.id,
        accion=accion,
        estado_anterior=estado_ant,
        estado_nuevo=estado_nuevo,
        observaciones=obs,
    )
    db.session.add(h)


def _parse_iso_dt(s):
    if not s:
        return None
    s = str(s).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    except ValueError:
        return None


def _entrevistador_id_from_payload(data, fallback):
    raw = data.get("id_entrevistador")
    if raw is None or raw == "":
        return fallback
    try:
        return int(raw)
    except (TypeError, ValueError):
        return fallback


def _color_evento(ent: Entrevista) -> str:
    if ent.resultado and ent.resultado != "pendiente":
        return "#9ca3af"
    return {
        "reclutador": "#2563eb",
        "jefe_area": "#7c3aed",
        "gerencia": "#0f766e",
    }.get(ent.tipo or "", "#2563eb")


@calendario_bp.route("/")
@login_required
def index():
    hoy = date.today()
    pendientes_hoy = (
        Entrevista.query.filter(
            Entrevista.resultado == "pendiente",
            Entrevista.fecha_programada.isnot(None),
            sa_func.date(Entrevista.fecha_programada) == hoy,
        ).count()
    )
    pendientes_total = Entrevista.query.filter(
        Entrevista.resultado == "pendiente",
        Entrevista.fecha_programada.isnot(None),
    ).count()

    ahora = datetime.utcnow()
    proximas = (
        Entrevista.query.filter(
            Entrevista.resultado == "pendiente",
            Entrevista.fecha_programada.isnot(None),
            Entrevista.fecha_programada >= ahora,
        )
        .order_by(Entrevista.fecha_programada.asc())
        .limit(8)
        .all()
    )
    usuarios = Usuario.query.filter_by(activo=True).order_by(Usuario.nombres).all()

    return render_template(
        "calendario/index.html",
        pendientes_hoy=pendientes_hoy,
        pendientes_total=pendientes_total,
        proximas=proximas,
        usuarios=usuarios,
    )


@calendario_bp.route("/eventos")
@login_required
def eventos():
    if not current_user.puede_ver_seleccion:
        return jsonify([]), 403

    start_dt = _parse_iso_dt(request.args.get("start"))
    end_dt = _parse_iso_dt(request.args.get("end"))

    q = Entrevista.query.options(
        joinedload(Entrevista.aplicacion).joinedload(Aplicacion.candidato),
        joinedload(Entrevista.aplicacion).joinedload(Aplicacion.vacante),
        joinedload(Entrevista.entrevistador),
    ).filter(Entrevista.fecha_programada.isnot(None))

    if start_dt and end_dt:
        q = q.filter(
            Entrevista.fecha_programada >= start_dt,
            Entrevista.fecha_programada < end_dt,
        )

    entrevistas = q.order_by(Entrevista.fecha_programada.asc()).all()
    out = []
    for ent in entrevistas:
        ap = ent.aplicacion
        cand = ap.candidato
        vac = ap.vacante
        ev = ent.entrevistador
        color = _color_evento(ent)
        out.append(
            {
                "id": str(ent.id),
                "title": f"{cand.nombre_completo} · {vac.titulo}",
                "start": ent.fecha_programada.isoformat(),
                "backgroundColor": color,
                "borderColor": color,
                "extendedProps": {
                    "app_id": ap.id,
                    "candidato": cand.nombre_completo,
                    "vacante": vac.titulo,
                    "area": vac.area or "",
                    "tipo": ent.tipo or "",
                    "lugar": ent.lugar or "",
                    "entrevistador": ev.nombre_completo if ev else "—",
                    "resultado": ent.resultado or "pendiente",
                },
            }
        )
    return jsonify(out)


@calendario_bp.route("/programar", methods=["POST"])
@login_required
def programar():
    if not current_user.es_reclutador:
        return jsonify({"ok": False, "error": "Sin permisos."}), 403

    data = request.get_json(silent=True) or {}
    try:
        app_id = int(data.get("app_id"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Aplicación no válida."}), 400

    aplicacion = db.session.get(Aplicacion, app_id)
    if not aplicacion:
        return jsonify({"ok": False, "error": "Aplicación no encontrada."}), 404

    tipo = (data.get("tipo") or "").strip()
    if tipo not in ("reclutador", "jefe_area", "gerencia"):
        return jsonify({"ok": False, "error": "Tipo de entrevista no válido."}), 400

    fecha_str = data.get("fecha_programada")
    fecha_prog = _parse_iso_dt(fecha_str) if fecha_str else None
    if not fecha_prog and fecha_str:
        try:
            fecha_prog = datetime.strptime(str(fecha_str)[:16], "%Y-%m-%dT%H:%M")
        except ValueError:
            fecha_prog = None
    if not fecha_prog:
        return jsonify({"ok": False, "error": "Fecha y hora requeridas."}), 400

    lugar = (data.get("lugar") or "").strip() or None
    reprogramar = bool(data.get("_reprogramar"))

    ent_default_eid = _entrevistador_id_from_payload(data, current_user.id)

    if reprogramar:
        ent = (
            Entrevista.query.filter_by(
                id_aplicacion=app_id,
                tipo=tipo,
                resultado="pendiente",
            )
            .order_by(Entrevista.id.desc())
            .first()
        )
        if not ent:
            return jsonify({"ok": False, "error": "No hay entrevista pendiente para reprogramar."}), 400
        ent.fecha_programada = fecha_prog
        if lugar is not None:
            ent.lugar = lugar
        db.session.commit()
        try:
            from services.email_service import notificar_entrevista_programada

            enviado = notificar_entrevista_programada(ent)
        except Exception:
            enviado = False
        return jsonify(
            {
                "ok": True,
                "email_enviado": bool(enviado),
                "candidato": aplicacion.candidato.nombre_completo,
            }
        )

    entrevista = Entrevista(
        id_aplicacion=app_id,
        tipo=tipo,
        fecha_programada=fecha_prog,
        lugar=lugar,
        id_entrevistador=ent_default_eid,
        resultado="pendiente",
    )
    db.session.add(entrevista)

    estado_ant = aplicacion.estado
    aplicacion.estado = "entrevista_programada"
    _registrar_historial(
        aplicacion,
        "Entrevista programada (calendario)",
        estado_ant,
        "entrevista_programada",
        obs=f"Tipo: {tipo}, Lugar: {lugar or '—'}",
    )
    db.session.commit()

    try:
        from services.email_service import notificar_entrevista_programada

        enviado = notificar_entrevista_programada(entrevista)
    except Exception:
        enviado = False

    return jsonify(
        {
            "ok": True,
            "email_enviado": bool(enviado),
            "candidato": aplicacion.candidato.nombre_completo,
        }
    )


@calendario_bp.route("/resultado/<int:ent_id>", methods=["POST"])
@login_required
def resultado_entrevista_cal(ent_id):
    if not current_user.es_reclutador:
        return jsonify({"ok": False, "error": "Sin permisos."}), 403

    entrevista = db.session.get(Entrevista, ent_id)
    if not entrevista:
        return jsonify({"ok": False, "error": "Entrevista no encontrada."}), 404

    data = request.get_json(silent=True) or {}
    resultado = (data.get("resultado") or "").strip()
    if resultado not in ("apto", "no_apto", "aplazado"):
        return jsonify({"ok": False, "error": "Resultado no válido."}), 400

    entrevista.resultado = resultado
    entrevista.observaciones = (data.get("observaciones") or "").strip() or None
    entrevista.fecha_realizada = datetime.utcnow()

    aplicacion = entrevista.aplicacion
    estado_ant = aplicacion.estado
    aplicacion.estado = "entrevista_realizada"
    _registrar_historial(
        aplicacion,
        f"Entrevista realizada — resultado: {resultado}",
        estado_ant,
        "entrevista_realizada",
        obs=entrevista.observaciones,
    )
    db.session.commit()
    return jsonify({"ok": True})
