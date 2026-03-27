"""
TalentFlow — Ciclo laboral de empleados (HR Core).
"""
from __future__ import annotations

import json
import csv
import io
from datetime import date, datetime
from urllib.error import URLError
from urllib.request import urlopen

from flask import Blueprint, Response, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_, text

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
    TareaOnboardingEmpleado,
    Usuario,
)
from services.hr_lifecycle import registrar_evento_laboral

empleados_bp = Blueprint("empleados", __name__, url_prefix="/empleados")


def _require_rrhh():
    if not current_user.is_authenticated or not current_user.es_rrhh:
        abort(403)


def _require_admin():
    if not current_user.is_authenticated or not current_user.es_admin:
        abort(403)


def _as_date(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_criterios_json(raw_json: str) -> list[dict]:
    try:
        data = json.loads(raw_json or "[]")
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido: {exc}") from exc
    if not isinstance(data, list) or not data:
        raise ValueError("Debes enviar una lista de criterios en JSON.")
    out = []
    for idx, c in enumerate(data, start=1):
        if not isinstance(c, dict):
            raise ValueError(f"Criterio #{idx} no es objeto JSON.")
        cid = str(c.get("id", "")).strip()
        texto = str(c.get("texto", "")).strip()
        if not cid or not texto:
            raise ValueError(f"Criterio #{idx} requiere id y texto.")
        try:
            peso = float(c.get("peso", 1))
            max_v = float(c.get("max", 5))
        except (TypeError, ValueError):
            raise ValueError(f"Criterio #{idx} tiene peso/max inválidos.") from None
        out.append({"id": cid, "texto": texto, "peso": peso, "max": max_v})
    return out


def _ensure_auditoria_catalogos_table() -> None:
    db.session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS auditoria_catalogos (
                id SERIAL PRIMARY KEY,
                entidad VARCHAR(50) NOT NULL,
                id_entidad INTEGER,
                accion VARCHAR(40) NOT NULL,
                detalle TEXT,
                id_usuario INTEGER REFERENCES usuarios(id),
                fecha_evento TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
            )
            """
        )
    )
    db.session.commit()


def _registrar_auditoria_catalogo(entidad: str, id_entidad: int | None, accion: str, detalle: str = "") -> None:
    _ensure_auditoria_catalogos_table()
    db.session.execute(
        text(
            """
            INSERT INTO auditoria_catalogos(entidad, id_entidad, accion, detalle, id_usuario)
            VALUES (:entidad, :id_entidad, :accion, :detalle, :id_usuario)
            """
        ),
        {
            "entidad": entidad,
            "id_entidad": id_entidad,
            "accion": accion,
            "detalle": (detalle or "")[:500],
            "id_usuario": current_user.id if getattr(current_user, "is_authenticated", False) else None,
        },
    )
    db.session.commit()


def _listar_auditoria_catalogos(
    limit: int = 60,
    entidad: str = "",
    accion: str = "",
    usuario_q: str = "",
    fecha_desde: str = "",
    fecha_hasta: str = "",
) -> list[dict]:
    _ensure_auditoria_catalogos_table()
    where = ["1=1"]
    params: dict = {"lim": int(limit)}
    if entidad:
        where.append("a.entidad = :entidad")
        params["entidad"] = entidad
    if accion:
        where.append("a.accion = :accion")
        params["accion"] = accion
    if usuario_q:
        where.append("(u.nombres ILIKE :uq OR u.apellidos ILIKE :uq OR u.correo ILIKE :uq)")
        params["uq"] = f"%{usuario_q}%"
    if fecha_desde:
        where.append("a.fecha_evento >= :fd")
        params["fd"] = f"{fecha_desde} 00:00:00"
    if fecha_hasta:
        where.append("a.fecha_evento <= :fh")
        params["fh"] = f"{fecha_hasta} 23:59:59"

    sql = f"""
        SELECT a.id, a.entidad, a.id_entidad, a.accion, a.detalle, a.fecha_evento,
               u.nombres, u.apellidos, u.correo
        FROM auditoria_catalogos a
        LEFT JOIN usuarios u ON u.id = a.id_usuario
        WHERE {' AND '.join(where)}
        ORDER BY a.id DESC
        LIMIT :lim
    """
    rows = db.session.execute(text(sql), params).mappings().all()
    out = []
    for r in rows:
        usuario = "Sistema"
        if r.get("nombres"):
            usuario = f"{r.get('nombres')} {r.get('apellidos') or ''}".strip()
        elif r.get("correo"):
            usuario = r.get("correo")
        out.append(
            {
                "id": r["id"],
                "entidad": r["entidad"],
                "id_entidad": r["id_entidad"],
                "accion": r["accion"],
                "detalle": r["detalle"] or "",
                "usuario": usuario,
                "fecha_evento": r["fecha_evento"],
            }
        )
    return out


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


@empleados_bp.route("/mi-espacio")
@login_required
def mi_espacio():
    emp = Empleado.query.filter_by(id_usuario=current_user.id).first()
    if not emp:
        flash("Tu usuario no tiene una ficha de empleado vinculada.", "info")
        return redirect(url_for("dashboard.index"))
    pendientes = [
        e
        for e in emp.evaluaciones_desempeno
        if getattr(e, "estado_aceptacion", "") == "pendiente_empleado"
    ]
    return render_template(
        "empleados/mi_espacio.html",
        empleado=emp,
        evals_pendientes=pendientes,
    )


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


@empleados_bp.route("/<int:emp_id>/onboarding/<int:tid>/toggle", methods=["POST"])
@login_required
def toggle_onboarding_tarea(emp_id: int, tid: int):
    _require_rrhh()
    emp = db.session.get(Empleado, emp_id)
    if not emp:
        abort(404)
    t = db.session.get(TareaOnboardingEmpleado, tid)
    if not t or t.id_empleado != emp.id:
        abort(404)
    t.hecha = not bool(t.hecha)
    db.session.commit()
    flash("Tarea de onboarding actualizada.", "success")
    return redirect(url_for("empleados.detalle", emp_id=emp.id))


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


def _catalogos_kpis() -> dict[str, int]:
    return {
        "kpis_sedes_total": Sede.query.count(),
        "kpis_cargos_total": Cargo.query.count(),
        "kpis_plantillas_total": PlantillaDesempenoCargo.query.count(),
    }


@empleados_bp.route("/admin/catalogos")
@login_required
def catalogos():
    _require_admin()
    return redirect(url_for("empleados.catalogos_sedes"))


@empleados_bp.route("/admin/catalogos/sedes")
@login_required
def catalogos_sedes():
    _require_admin()
    q = (request.args.get("q") or "").strip()
    page = max(1, request.args.get("page", default=1, type=int))
    per_page = 10

    sedes_q = Sede.query
    if q:
        like = f"%{q}%"
        sedes_q = sedes_q.filter(or_(Sede.codigo.ilike(like), Sede.nombre.ilike(like), Sede.ciudad.ilike(like)))
    sedes = sedes_q.order_by(Sede.activa.desc(), Sede.nombre.asc()).paginate(page=page, per_page=per_page, error_out=False)

    ctx = _catalogos_kpis()
    return render_template(
        "empleados/catalogos/sedes.html",
        catalog_section="sedes",
        sedes=sedes,
        q=q,
        **ctx,
    )


@empleados_bp.route("/admin/catalogos/cargos")
@login_required
def catalogos_cargos():
    _require_admin()
    q = (request.args.get("q") or "").strip()
    page = max(1, request.args.get("page", default=1, type=int))
    per_page = 10

    cargos_q = Cargo.query
    if q:
        like = f"%{q}%"
        cargos_q = cargos_q.filter(
            or_(Cargo.codigo.ilike(like), Cargo.nombre.ilike(like), Cargo.area.ilike(like), Cargo.nivel.ilike(like))
        )
    cargos = cargos_q.order_by(Cargo.activo.desc(), Cargo.nombre.asc()).paginate(page=page, per_page=per_page, error_out=False)

    ctx = _catalogos_kpis()
    return render_template(
        "empleados/catalogos/cargos.html",
        catalog_section="cargos",
        cargos=cargos,
        q=q,
        **ctx,
    )


@empleados_bp.route("/admin/catalogos/plantillas-desempeno")
@login_required
def catalogos_plantillas():
    _require_admin()
    q = (request.args.get("q") or "").strip()
    page = max(1, request.args.get("page", default=1, type=int))
    per_page = 10

    tpl_q = PlantillaDesempenoCargo.query
    if q:
        like = f"%{q}%"
        tpl_q = tpl_q.filter(PlantillaDesempenoCargo.nombre.ilike(like))
    plantillas = tpl_q.order_by(
        PlantillaDesempenoCargo.activa.desc(),
        PlantillaDesempenoCargo.id.desc(),
    ).paginate(page=page, per_page=per_page, error_out=False)

    cargos_select = Cargo.query.filter_by(activo=True).order_by(Cargo.nombre.asc()).all()
    ctx = _catalogos_kpis()
    return render_template(
        "empleados/catalogos/plantillas.html",
        catalog_section="plantillas",
        plantillas=plantillas,
        cargos_select=cargos_select,
        q=q,
        **ctx,
    )


@empleados_bp.route("/admin/catalogos/auditoria")
@login_required
def catalogos_auditoria():
    _require_admin()
    aud_entidad = (request.args.get("aud_entidad") or "").strip()
    aud_accion = (request.args.get("aud_accion") or "").strip()
    aud_usuario = (request.args.get("aud_usuario") or "").strip()
    aud_desde = (request.args.get("aud_desde") or "").strip()
    aud_hasta = (request.args.get("aud_hasta") or "").strip()

    auditoria = _listar_auditoria_catalogos(
        limit=120,
        entidad=aud_entidad,
        accion=aud_accion,
        usuario_q=aud_usuario,
        fecha_desde=aud_desde,
        fecha_hasta=aud_hasta,
    )
    ctx = _catalogos_kpis()
    return render_template(
        "empleados/catalogos/auditoria.html",
        catalog_section="auditoria",
        auditoria=auditoria,
        aud_entidad=aud_entidad,
        aud_accion=aud_accion,
        aud_usuario=aud_usuario,
        aud_desde=aud_desde,
        aud_hasta=aud_hasta,
        **ctx,
    )


@empleados_bp.route("/admin/sedes", methods=["POST"])
@login_required
def crear_sede():
    _require_admin()
    codigo = (request.form.get("codigo") or "").strip().upper()
    nombre = (request.form.get("nombre") or "").strip()
    if not codigo or not nombre:
        flash("Código y nombre de sede son obligatorios.", "danger")
        return redirect(url_for("empleados.catalogos_sedes"))
    if Sede.query.filter_by(codigo=codigo).first():
        flash("Ya existe una sede con ese código.", "warning")
        return redirect(url_for("empleados.catalogos_sedes"))
    sede = Sede(
        codigo=codigo,
        nombre=nombre,
        ciudad=(request.form.get("ciudad") or "").strip() or None,
        direccion=(request.form.get("direccion") or "").strip() or None,
        activa=bool(request.form.get("activa")),
    )
    db.session.add(sede)
    db.session.commit()
    _registrar_auditoria_catalogo("sede", sede.id, "crear", f"Código={sede.codigo}; Nombre={sede.nombre}")
    flash("Sede creada.", "success")
    return redirect(url_for("empleados.catalogos_sedes"))


@empleados_bp.route("/admin/cargos", methods=["POST"])
@login_required
def crear_cargo():
    _require_admin()
    codigo = (request.form.get("codigo") or "").strip().upper()
    nombre = (request.form.get("nombre") or "").strip()
    if not codigo or not nombre:
        flash("Código y nombre de cargo son obligatorios.", "danger")
        return redirect(url_for("empleados.catalogos_cargos"))
    if Cargo.query.filter_by(codigo=codigo).first():
        flash("Ya existe un cargo con ese código.", "warning")
        return redirect(url_for("empleados.catalogos_cargos"))
    cargo = Cargo(
        codigo=codigo,
        nombre=nombre,
        area=(request.form.get("area") or "").strip() or None,
        nivel=(request.form.get("nivel") or "").strip() or None,
        competencias_json=(request.form.get("competencias_json") or "").strip() or None,
        activo=bool(request.form.get("activo")),
    )
    db.session.add(cargo)
    db.session.commit()
    _registrar_auditoria_catalogo("cargo", cargo.id, "crear", f"Código={cargo.codigo}; Nombre={cargo.nombre}")
    flash("Cargo creado.", "success")
    return redirect(url_for("empleados.catalogos_cargos"))


@empleados_bp.route("/admin/plantillas-desempeno", methods=["POST"])
@login_required
def crear_plantilla_desempeno():
    _require_admin()
    id_cargo = request.form.get("id_cargo", type=int)
    nombre = (request.form.get("nombre") or "").strip()
    version = request.form.get("version", type=int) or 1
    activa = bool(request.form.get("activa"))
    criterios_json = (request.form.get("criterios_json") or "").strip()
    criterios_url = (request.form.get("criterios_url") or "").strip()

    if not id_cargo or not nombre:
        flash("Cargo y nombre de plantilla son obligatorios.", "danger")
        return redirect(url_for("empleados.catalogos_plantillas"))
    if not db.session.get(Cargo, id_cargo):
        flash("Cargo inválido para plantilla.", "danger")
        return redirect(url_for("empleados.catalogos_plantillas"))

    if not criterios_json and criterios_url:
        try:
            with urlopen(criterios_url, timeout=8) as r:
                criterios_json = r.read().decode("utf-8")
        except (URLError, TimeoutError, ValueError) as exc:
            flash(f"No se pudo cargar JSON desde URL: {exc}", "danger")
            return redirect(url_for("empleados.catalogos_plantillas"))

    try:
        criterios = _parse_criterios_json(criterios_json)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("empleados.catalogos_plantillas"))

    existe = PlantillaDesempenoCargo.query.filter_by(
        id_cargo=id_cargo, nombre=nombre, version=version
    ).first()
    if existe:
        flash("Ya existe una plantilla con ese nombre y versión para el cargo.", "warning")
        return redirect(url_for("empleados.catalogos_plantillas"))

    p = PlantillaDesempenoCargo(
        id_cargo=id_cargo,
        nombre=nombre,
        version=version,
        criterios_json=json.dumps(criterios, ensure_ascii=False),
        activa=activa,
    )
    db.session.add(p)
    db.session.commit()
    _registrar_auditoria_catalogo(
        "plantilla_desempeno",
        p.id,
        "crear",
        f"Cargo={p.id_cargo}; Nombre={p.nombre}; Version={p.version}",
    )
    flash("Plantilla de desempeño creada.", "success")
    return redirect(url_for("empleados.catalogos_plantillas"))


@empleados_bp.route("/admin/plantillas-desempeno/<int:pid>/toggle", methods=["POST"])
@login_required
def toggle_plantilla_desempeno(pid: int):
    _require_admin()
    p = db.session.get(PlantillaDesempenoCargo, pid)
    if not p:
        abort(404)
    p.activa = not p.activa
    db.session.commit()
    _registrar_auditoria_catalogo(
        "plantilla_desempeno",
        p.id,
        "toggle_estado",
        f"Activa={p.activa}",
    )
    flash("Estado de plantilla actualizado.", "info")
    return redirect(url_for("empleados.catalogos_plantillas"))


@empleados_bp.route("/admin/sedes/<int:sid>/editar", methods=["POST"])
@login_required
def editar_sede(sid: int):
    _require_admin()
    s = db.session.get(Sede, sid)
    if not s:
        abort(404)

    codigo = (request.form.get("codigo") or "").strip().upper()
    nombre = (request.form.get("nombre") or "").strip()
    if not codigo or not nombre:
        flash("Código y nombre son obligatorios para sede.", "danger")
        return redirect(url_for("empleados.catalogos_sedes"))

    dup = Sede.query.filter(Sede.codigo == codigo, Sede.id != s.id).first()
    if dup:
        flash("Ya existe otra sede con ese código.", "warning")
        return redirect(url_for("empleados.catalogos_sedes"))

    s.codigo = codigo
    s.nombre = nombre
    s.ciudad = (request.form.get("ciudad") or "").strip() or None
    s.direccion = (request.form.get("direccion") or "").strip() or None
    s.activa = bool(request.form.get("activa"))
    db.session.commit()
    _registrar_auditoria_catalogo("sede", s.id, "editar", f"Código={s.codigo}; Nombre={s.nombre}; Activa={s.activa}")
    flash("Sede actualizada.", "success")
    return redirect(url_for("empleados.catalogos_sedes"))


@empleados_bp.route("/admin/sedes/<int:sid>/eliminar", methods=["POST"])
@login_required
def eliminar_sede(sid: int):
    _require_admin()
    s = db.session.get(Sede, sid)
    if not s:
        abort(404)
    if AsignacionLaboral.query.filter_by(id_sede=s.id).first():
        flash(
            "No se puede eliminar la sede porque tiene asignaciones históricas. Desactívala en su lugar.",
            "warning",
        )
        return redirect(url_for("empleados.catalogos_sedes"))
    sid_del, cod_del = s.id, s.codigo
    db.session.delete(s)
    db.session.commit()
    _registrar_auditoria_catalogo("sede", sid_del, "eliminar", f"Código={cod_del}")
    flash("Sede eliminada.", "info")
    return redirect(url_for("empleados.catalogos_sedes"))


@empleados_bp.route("/admin/cargos/<int:cid>/editar", methods=["POST"])
@login_required
def editar_cargo(cid: int):
    _require_admin()
    c = db.session.get(Cargo, cid)
    if not c:
        abort(404)

    codigo = (request.form.get("codigo") or "").strip().upper()
    nombre = (request.form.get("nombre") or "").strip()
    if not codigo or not nombre:
        flash("Código y nombre son obligatorios para cargo.", "danger")
        return redirect(url_for("empleados.catalogos_cargos"))

    dup = Cargo.query.filter(Cargo.codigo == codigo, Cargo.id != c.id).first()
    if dup:
        flash("Ya existe otro cargo con ese código.", "warning")
        return redirect(url_for("empleados.catalogos_cargos"))

    c.codigo = codigo
    c.nombre = nombre
    c.area = (request.form.get("area") or "").strip() or None
    c.nivel = (request.form.get("nivel") or "").strip() or None
    c.competencias_json = (request.form.get("competencias_json") or "").strip() or None
    c.activo = bool(request.form.get("activo"))
    db.session.commit()
    _registrar_auditoria_catalogo("cargo", c.id, "editar", f"Código={c.codigo}; Nombre={c.nombre}; Activo={c.activo}")
    flash("Cargo actualizado.", "success")
    return redirect(url_for("empleados.catalogos_cargos"))


@empleados_bp.route("/admin/cargos/<int:cid>/eliminar", methods=["POST"])
@login_required
def eliminar_cargo(cid: int):
    _require_admin()
    c = db.session.get(Cargo, cid)
    if not c:
        abort(404)
    if AsignacionLaboral.query.filter_by(id_cargo=c.id).first():
        flash(
            "No se puede eliminar el cargo porque tiene asignaciones históricas. Desactívalo en su lugar.",
            "warning",
        )
        return redirect(url_for("empleados.catalogos_cargos"))
    if PlantillaDesempenoCargo.query.filter_by(id_cargo=c.id).first():
        flash(
            "No se puede eliminar el cargo porque tiene plantillas de desempeño asociadas.",
            "warning",
        )
        return redirect(url_for("empleados.catalogos_cargos"))
    cid_del, cod_del = c.id, c.codigo
    db.session.delete(c)
    db.session.commit()
    _registrar_auditoria_catalogo("cargo", cid_del, "eliminar", f"Código={cod_del}")
    flash("Cargo eliminado.", "info")
    return redirect(url_for("empleados.catalogos_cargos"))


@empleados_bp.route("/admin/plantillas-desempeno/<int:pid>/editar", methods=["POST"])
@login_required
def editar_plantilla_desempeno(pid: int):
    _require_admin()
    p = db.session.get(PlantillaDesempenoCargo, pid)
    if not p:
        abort(404)

    id_cargo = request.form.get("id_cargo", type=int)
    nombre = (request.form.get("nombre") or "").strip()
    version = request.form.get("version", type=int) or 1
    activa = bool(request.form.get("activa"))
    criterios_json = (request.form.get("criterios_json") or "").strip()
    criterios_url = (request.form.get("criterios_url") or "").strip()

    if not id_cargo or not nombre:
        flash("Cargo y nombre son obligatorios para plantilla.", "danger")
        return redirect(url_for("empleados.catalogos_plantillas"))
    if not db.session.get(Cargo, id_cargo):
        flash("Cargo inválido para plantilla.", "danger")
        return redirect(url_for("empleados.catalogos_plantillas"))

    if not criterios_json and criterios_url:
        try:
            with urlopen(criterios_url, timeout=8) as r:
                criterios_json = r.read().decode("utf-8")
        except (URLError, TimeoutError, ValueError) as exc:
            flash(f"No se pudo cargar JSON desde URL: {exc}", "danger")
            return redirect(url_for("empleados.catalogos_plantillas"))

    try:
        criterios = _parse_criterios_json(criterios_json)
    except ValueError as exc:
        flash(str(exc), "danger")
        return redirect(url_for("empleados.catalogos_plantillas"))

    dup = PlantillaDesempenoCargo.query.filter(
        PlantillaDesempenoCargo.id_cargo == id_cargo,
        PlantillaDesempenoCargo.nombre == nombre,
        PlantillaDesempenoCargo.version == version,
        PlantillaDesempenoCargo.id != p.id,
    ).first()
    if dup:
        flash("Ya existe otra plantilla con ese nombre y versión para el cargo.", "warning")
        return redirect(url_for("empleados.catalogos_plantillas"))

    p.id_cargo = id_cargo
    p.nombre = nombre
    p.version = version
    p.activa = activa
    p.criterios_json = json.dumps(criterios, ensure_ascii=False)
    db.session.commit()
    _registrar_auditoria_catalogo(
        "plantilla_desempeno",
        p.id,
        "editar",
        f"Cargo={p.id_cargo}; Nombre={p.nombre}; Version={p.version}; Activa={p.activa}",
    )
    flash("Plantilla actualizada.", "success")
    return redirect(url_for("empleados.catalogos_plantillas"))


@empleados_bp.route("/admin/plantillas-desempeno/<int:pid>/eliminar", methods=["POST"])
@login_required
def eliminar_plantilla_desempeno(pid: int):
    _require_admin()
    p = db.session.get(PlantillaDesempenoCargo, pid)
    if not p:
        abort(404)
    if EvaluacionDesempeno.query.filter_by(id_plantilla=p.id).first():
        flash(
            "No se puede eliminar la plantilla porque ya tiene evaluaciones registradas.",
            "warning",
        )
        return redirect(url_for("empleados.catalogos_plantillas"))
    pid_del, nom_del = p.id, p.nombre
    db.session.delete(p)
    db.session.commit()
    _registrar_auditoria_catalogo("plantilla_desempeno", pid_del, "eliminar", f"Nombre={nom_del}")
    flash("Plantilla eliminada.", "info")
    return redirect(url_for("empleados.catalogos_plantillas"))


@empleados_bp.route("/admin/auditoria/exportar")
@login_required
def exportar_auditoria_catalogos():
    _require_admin()
    aud_entidad = (request.args.get("aud_entidad") or "").strip()
    aud_accion = (request.args.get("aud_accion") or "").strip()
    aud_usuario = (request.args.get("aud_usuario") or "").strip()
    aud_desde = (request.args.get("aud_desde") or "").strip()
    aud_hasta = (request.args.get("aud_hasta") or "").strip()
    rows = _listar_auditoria_catalogos(
        limit=10000,
        entidad=aud_entidad,
        accion=aud_accion,
        usuario_q=aud_usuario,
        fecha_desde=aud_desde,
        fecha_hasta=aud_hasta,
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["fecha", "entidad", "id_entidad", "accion", "detalle", "usuario"])
    for r in rows:
        writer.writerow(
            [
                r["fecha_evento"].strftime("%Y-%m-%d %H:%M:%S") if r["fecha_evento"] else "",
                r["entidad"],
                r["id_entidad"] or "",
                r["accion"],
                r["detalle"],
                r["usuario"],
            ]
        )
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=auditoria_catalogos.csv"},
    )
