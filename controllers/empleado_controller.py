"""
TalentFlow — Ciclo laboral de empleados (HR Core).
"""
from __future__ import annotations

import json
from datetime import date, datetime

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import (
    AsignacionLaboral,
    Cargo,
    Desvinculacion,
    Empleado,
    EvaluacionDesempeno,
    MovimientoLaboral,
    NovedadDisciplinaria,
    PlantillaDesempenoCargo,
    Sede,
    TIPOS_MOVIMIENTO_LABORAL,
    Usuario,
)
from services.hr_lifecycle import registrar_evento_laboral

empleados_bp = Blueprint("empleados", __name__, url_prefix="/empleados")


def _require_rrhh():
    if not current_user.is_authenticated or not current_user.es_rrhh:
        abort(403)


def _as_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


@empleados_bp.route("/")
@login_required
def index():
    if not current_user.es_rrhh:
        abort(403)

    estado = request.args.get("estado", "").strip()
    q = Empleado.query
    if estado:
        q = q.filter_by(estado_laboral=estado)
    empleados = q.order_by(Empleado.fecha_ingreso.desc(), Empleado.id.desc()).all()
    return render_template("empleados/index.html", empleados=empleados, estado=estado)


@empleados_bp.route("/<int:emp_id>")
@login_required
def detalle(emp_id: int):
    emp = db.session.get(Empleado, emp_id)
    if not emp:
        abort(404)
    if not current_user.es_rrhh and (not emp.id_usuario or emp.id_usuario != current_user.id):
        abort(403)

    sedes = Sede.query.filter_by(activa=True).order_by(Sede.nombre).all()
    cargos = Cargo.query.filter_by(activo=True).order_by(Cargo.nombre).all()
    jefes = Usuario.query.filter_by(activo=True).order_by(Usuario.nombres).all()
    plantillas = PlantillaDesempenoCargo.query.filter_by(activa=True).order_by(PlantillaDesempenoCargo.nombre).all()
    return render_template(
        "empleados/detalle.html",
        empleado=emp,
        sedes=sedes,
        cargos=cargos,
        jefes=jefes,
        plantillas=plantillas,
        tipos_movimiento=TIPOS_MOVIMIENTO_LABORAL,
    )


@empleados_bp.route("/<int:emp_id>/movimiento", methods=["POST"])
@login_required
def registrar_movimiento(emp_id: int):
    _require_rrhh()
    emp = db.session.get(Empleado, emp_id)
    if not emp:
        abort(404)

    tipo = (request.form.get("tipo") or "").strip()
    id_cargo = request.form.get("id_cargo", type=int)
    id_sede = request.form.get("id_sede", type=int)
    id_jefe = request.form.get("id_jefe", type=int)
    fecha = _as_date(request.form.get("fecha_movimiento")) or date.today()
    motivo = (request.form.get("motivo") or "").strip()

    if not tipo or not id_cargo or not id_sede:
        flash("Tipo de movimiento, cargo y sede son obligatorios.", "danger")
        return redirect(url_for("empleados.detalle", emp_id=emp.id))

    cargo = db.session.get(Cargo, id_cargo)
    sede = db.session.get(Sede, id_sede)
    if not cargo or not sede:
        flash("Cargo o sede no válidos.", "danger")
        return redirect(url_for("empleados.detalle", emp_id=emp.id))

    anterior = (
        AsignacionLaboral.query.filter_by(id_empleado=emp.id, es_actual=True)
        .order_by(AsignacionLaboral.id.desc())
        .first()
    )
    if anterior:
        anterior.es_actual = False
        anterior.fecha_fin = fecha

    nueva = AsignacionLaboral(
        id_empleado=emp.id,
        id_cargo=id_cargo,
        id_sede=id_sede,
        id_jefe=id_jefe,
        fecha_inicio=fecha,
        es_actual=True,
        observaciones=motivo or None,
    )
    db.session.add(nueva)
    db.session.flush()

    mov = MovimientoLaboral(
        id_empleado=emp.id,
        tipo=tipo,
        id_asignacion_anterior=anterior.id if anterior else None,
        id_asignacion_nueva=nueva.id,
        fecha_movimiento=fecha,
        motivo=motivo,
        id_usuario=current_user.id,
    )
    db.session.add(mov)
    registrar_evento_laboral(
        emp,
        "movimiento_laboral",
        f"{tipo}: {cargo.nombre} en {sede.nombre}",
        current_user.id,
        {"id_movimiento": mov.id, "tipo": tipo},
    )
    db.session.commit()
    flash("Movimiento laboral registrado.", "success")
    return redirect(url_for("empleados.detalle", emp_id=emp.id))


@empleados_bp.route("/<int:emp_id>/evaluacion", methods=["POST"])
@login_required
def registrar_evaluacion(emp_id: int):
    _require_rrhh()
    emp = db.session.get(Empleado, emp_id)
    if not emp:
        abort(404)

    plantilla_id = request.form.get("id_plantilla", type=int)
    plantilla = db.session.get(PlantillaDesempenoCargo, plantilla_id) if plantilla_id else None
    if not plantilla:
        flash("Plantilla de desempeño no válida.", "danger")
        return redirect(url_for("empleados.detalle", emp_id=emp.id))

    try:
        criterios = json.loads(plantilla.criterios_json or "[]")
    except json.JSONDecodeError:
        criterios = []
    if not criterios:
        flash("La plantilla no tiene criterios válidos.", "danger")
        return redirect(url_for("empleados.detalle", emp_id=emp.id))

    detalle = {}
    ponderado = 0.0
    total_max = 0.0
    for c in criterios:
        cid = str(c.get("id", "")).strip()
        if not cid:
            continue
        max_v = float(c.get("max", 5))
        peso = float(c.get("peso", 1))
        raw = request.form.get(f"criterio_{cid}")
        try:
            val = float(raw)
        except (TypeError, ValueError):
            val = 0.0
        val = max(0.0, min(val, max_v))
        detalle[cid] = {"valor": val, "max": max_v, "peso": peso, "texto": c.get("texto", cid)}
        ponderado += val * peso
        total_max += max_v * peso
    puntaje = round((ponderado / total_max) * 100, 2) if total_max > 0 else 0.0

    ev = EvaluacionDesempeno(
        id_empleado=emp.id,
        id_plantilla=plantilla.id,
        periodo=(request.form.get("periodo") or "").strip() or f"{date.today().year}-Q{((date.today().month - 1) // 3) + 1}",
        id_jefe_evaluador=request.form.get("id_jefe_evaluador", type=int) or current_user.id,
        puntaje_total=puntaje,
        detalle_json=json.dumps(detalle, ensure_ascii=False),
        comentario_jefe=request.form.get("comentario_jefe"),
    )
    db.session.add(ev)
    db.session.flush()
    registrar_evento_laboral(
        emp,
        "evaluacion_desempeno",
        f"Evaluación de desempeño registrada (puntaje {puntaje}).",
        current_user.id,
        {"id_evaluacion": ev.id, "puntaje_total": puntaje},
    )
    db.session.commit()
    flash("Evaluación de desempeño registrada.", "success")
    return redirect(url_for("empleados.detalle", emp_id=emp.id))


@empleados_bp.route("/evaluacion/<int:ev_id>/aceptar", methods=["POST"])
@login_required
def aceptar_evaluacion(ev_id: int):
    ev = db.session.get(EvaluacionDesempeno, ev_id)
    if not ev:
        abort(404)
    empleado = ev.empleado
    if not current_user.es_rrhh and (not empleado.id_usuario or empleado.id_usuario != current_user.id):
        abort(403)

    accion = (request.form.get("accion") or "").strip()
    if accion not in ("aceptar", "rechazar"):
        flash("Acción no válida.", "danger")
        return redirect(url_for("empleados.detalle", emp_id=empleado.id))

    ev.estado_aceptacion = "aceptada" if accion == "aceptar" else "rechazada"
    ev.comentario_empleado = request.form.get("comentario_empleado")
    ev.fecha_aceptacion = datetime.utcnow()
    registrar_evento_laboral(
        empleado,
        "aceptacion_evaluacion",
        f"Evaluación {accion} por empleado.",
        current_user.id,
        {"id_evaluacion": ev.id, "accion": accion},
    )
    db.session.commit()
    flash("Respuesta de evaluación registrada.", "success")
    return redirect(url_for("empleados.detalle", emp_id=empleado.id))


@empleados_bp.route("/<int:emp_id>/disciplina", methods=["POST"])
@login_required
def registrar_disciplina(emp_id: int):
    _require_rrhh()
    emp = db.session.get(Empleado, emp_id)
    if not emp:
        abort(404)

    nov = NovedadDisciplinaria(
        id_empleado=emp.id,
        tipo=(request.form.get("tipo") or "").strip() or "falta",
        severidad=(request.form.get("severidad") or "").strip() or None,
        descripcion=(request.form.get("descripcion") or "").strip(),
        estado=(request.form.get("estado") or "").strip() or "registrada",
        fecha_falta=_as_date(request.form.get("fecha_falta")) or date.today(),
        id_reporta=current_user.id,
        id_aprueba=request.form.get("id_aprueba", type=int),
        sancion=request.form.get("sancion"),
    )
    if not nov.descripcion:
        flash("La descripción de la novedad es obligatoria.", "danger")
        return redirect(url_for("empleados.detalle", emp_id=emp.id))
    db.session.add(nov)
    registrar_evento_laboral(emp, "novedad_disciplinaria", "Novedad disciplinaria registrada.", current_user.id)
    db.session.commit()
    flash("Novedad disciplinaria registrada.", "success")
    return redirect(url_for("empleados.detalle", emp_id=emp.id))


@empleados_bp.route("/<int:emp_id>/desvincular", methods=["POST"])
@login_required
def desvincular(emp_id: int):
    _require_rrhh()
    emp = db.session.get(Empleado, emp_id)
    if not emp:
        abort(404)

    tipo = (request.form.get("tipo") or "").strip()
    fecha_ef = _as_date(request.form.get("fecha_efectiva")) or date.today()
    if not tipo:
        flash("Tipo de salida obligatorio.", "danger")
        return redirect(url_for("empleados.detalle", emp_id=emp.id))

    reg = Desvinculacion(
        id_empleado=emp.id,
        tipo=tipo,
        causa=request.form.get("causa"),
        fecha_efectiva=fecha_ef,
        documento_ref=request.form.get("documento_ref"),
        id_usuario=current_user.id,
    )
    db.session.add(reg)

    emp.estado_laboral = "despedido" if tipo == "despido" else "retiro"
    emp.fecha_salida = fecha_ef
    emp.motivo_salida = tipo

    actual = (
        AsignacionLaboral.query.filter_by(id_empleado=emp.id, es_actual=True)
        .order_by(AsignacionLaboral.id.desc())
        .first()
    )
    if actual:
        actual.es_actual = False
        actual.fecha_fin = fecha_ef

    registrar_evento_laboral(
        emp,
        "desvinculacion",
        f"Empleado desvinculado ({tipo}).",
        current_user.id,
        {"tipo": tipo, "fecha_efectiva": fecha_ef.isoformat()},
    )
    db.session.commit()
    flash("Desvinculación registrada.", "warning")
    return redirect(url_for("empleados.detalle", emp_id=emp.id))


@empleados_bp.route("/api/<int:emp_id>/timeline")
@login_required
def api_timeline(emp_id: int):
    emp = db.session.get(Empleado, emp_id)
    if not emp:
        return jsonify({"ok": False, "error": "No encontrado"}), 404
    if not current_user.es_rrhh and (not emp.id_usuario or emp.id_usuario != current_user.id):
        return jsonify({"ok": False, "error": "Sin permisos"}), 403

    data = [
        {
            "id": ev.id,
            "tipo": ev.tipo_evento,
            "descripcion": ev.descripcion,
            "fecha": ev.fecha_evento.isoformat() if ev.fecha_evento else None,
        }
        for ev in sorted(emp.eventos, key=lambda x: x.fecha_evento or datetime.min, reverse=True)
    ]
    return jsonify({"ok": True, "timeline": data})
