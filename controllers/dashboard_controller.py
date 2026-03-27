"""
TalentFlow — Dashboard y Reportes
"""

import csv
import io
from collections import defaultdict
from datetime import datetime, timedelta

from flask import Blueprint, Response, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from sqlalchemy import case, func

from extensions import db
from models import (
    Aplicacion,
    AsignacionLaboral,
    Cargo,
    Candidato,
    Desvinculacion,
    Empleado,
    EvaluacionDesempeno,
    ESTADOS_APLICACION,
    ESTADOS_DICT,
    HistorialProceso,
    NovedadDisciplinaria,
    Sede,
    Vacante,
)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/")
reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    total_candidatos = Candidato.query.filter_by(activo=True).count()
    total_vacantes = Vacante.query.filter_by(estado="abierta").count()
    total_aplicaciones = Aplicacion.query.count()
    contratados = Aplicacion.query.filter_by(estado="contratado").count()
    rechazados = Aplicacion.query.filter_by(estado="rechazado").count()
    en_proceso = Aplicacion.query.filter(
        Aplicacion.estado.notin_(["contratado", "rechazado"])
    ).count()

    # Candidatos por estado (para gráfica)
    estados_data = {}
    for codigo, nombre in ESTADOS_APLICACION:
        count = Aplicacion.query.filter_by(estado=codigo).count()
        if count > 0:
            estados_data[nombre] = count

    ultimas_aplicaciones = (
        Aplicacion.query
        .order_by(Aplicacion.fecha_aplicacion.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "dashboard/index.html",
        total_candidatos=total_candidatos,
        total_vacantes=total_vacantes,
        total_aplicaciones=total_aplicaciones,
        contratados=contratados,
        rechazados=rechazados,
        en_proceso=en_proceso,
        estados_data=estados_data,
        ultimas_aplicaciones=ultimas_aplicaciones,
    )


@dashboard_bp.route("/buscar")
@login_required
def busqueda_global():
    q = (request.args.get("q") or "").strip()
    if not q:
        return redirect(url_for("dashboard.index"))
    like = f"%{q}%"

    candidatos = []
    vacantes = []
    if current_user.puede_ver_seleccion:
        candidatos = (
            Candidato.query.filter(
                db.or_(
                    Candidato.cedula.ilike(like),
                    Candidato.nombres.ilike(like),
                    Candidato.apellidos.ilike(like),
                    Candidato.correo.ilike(like),
                )
            )
            .order_by(Candidato.fecha_registro.desc())
            .limit(8)
            .all()
        )
        vacantes = (
            Vacante.query.filter(
                db.or_(
                    Vacante.titulo.ilike(like),
                    Vacante.area.ilike(like),
                    Vacante.ciudad.ilike(like),
                )
            )
            .order_by(Vacante.fecha_creacion.desc())
            .limit(8)
            .all()
        )

    empleados = []
    if current_user.es_rrhh:
        empleados = (
            Empleado.query.join(Candidato, Candidato.cedula == Empleado.cedula)
            .filter(
                db.or_(
                    Empleado.cedula.ilike(like),
                    Candidato.nombres.ilike(like),
                    Candidato.apellidos.ilike(like),
                )
            )
            .order_by(Empleado.id.desc())
            .limit(8)
            .all()
        )

    return render_template(
        "dashboard/busqueda.html",
        q=q,
        candidatos=candidatos,
        vacantes=vacantes,
        empleados=empleados,
    )


@dashboard_bp.route("/notificaciones/marcar-vista", methods=["POST"])
@login_required
def marcar_notificacion_vista():
    notif_key = (request.form.get("notif_key") or "").strip()
    if not notif_key:
        return jsonify({"ok": False, "error": "notif_key requerido"}), 400
    try:
        from services.notifications_store import mark_seen

        mark_seen(current_user.id, notif_key)
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@dashboard_bp.route("/notificaciones/marcar-todas-vistas", methods=["POST"])
@login_required
def marcar_todas_notificaciones_vistas():
    notif_keys = request.form.getlist("notif_keys[]")
    if not notif_keys:
        return jsonify({"ok": True, "count": 0})
    try:
        from services.notifications_store import mark_many_seen

        count = mark_many_seen(current_user.id, notif_keys)
        return jsonify({"ok": True, "count": count})
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@dashboard_bp.route("/dashboard/api/hr/resumen")
@login_required
def api_hr_resumen():
    if not current_user.es_rrhh:
        return jsonify({"error": "Solo RRHH/administración."}), 403

    activos = Empleado.query.filter_by(estado_laboral="activo").count()
    retirados = Empleado.query.filter(Empleado.estado_laboral.in_(["retiro", "despedido"])).count()
    asignaciones_historicas = (
        db.session.query(func.count()).select_from(AsignacionLaboral).scalar() or 0
    )
    desv = Desvinculacion.query.count()
    evals = EvaluacionDesempeno.query.count()
    novedades = NovedadDisciplinaria.query.count()
    return jsonify(
        {
            "activos": activos,
            "retirados": retirados,
            "asignaciones_historicas": int(asignaciones_historicas),
            "desvinculaciones": desv,
            "evaluaciones": evals,
            "novedades_disciplinarias": novedades,
        }
    )


@dashboard_bp.route("/dashboard/api/embudo")
@login_required
def api_embudo():
    """Conteos por estado del pipeline (orden definido en ESTADOS_APLICACION)."""
    if not current_user.puede_ver_seleccion:
        return jsonify({"error": "Sin permiso."}), 403

    data = []
    for codigo, nombre in ESTADOS_APLICACION:
        count = Aplicacion.query.filter_by(estado=codigo).count()
        data.append({"codigo": codigo, "nombre": nombre, "count": count})
    return jsonify(data)


@dashboard_bp.route("/dashboard/api/conversion-vacante")
@login_required
def api_conversion_vacante():
    """Aplicaciones por vacante y tasa contratados / total."""
    if not current_user.puede_ver_seleccion:
        return jsonify({"error": "Sin permiso."}), 403

    contratado_case = case((Aplicacion.estado == "contratado", 1), else_=0)
    rows = (
        db.session.query(
            Vacante.id,
            Vacante.titulo,
            func.count(Aplicacion.id).label("total"),
            func.coalesce(func.sum(contratado_case), 0).label("contratados"),
        )
        .select_from(Vacante)
        .outerjoin(Aplicacion, Vacante.id == Aplicacion.id_vacante)
        .group_by(Vacante.id, Vacante.titulo)
        .having(func.count(Aplicacion.id) > 0)
        .order_by(func.count(Aplicacion.id).desc())
        .limit(20)
        .all()
    )
    out = []
    for vid, titulo, total, contr in rows:
        total = int(total or 0)
        contr = int(contr or 0)
        pct = round(100.0 * contr / total, 1) if total else 0.0
        out.append(
            {
                "id": vid,
                "titulo": titulo,
                "total": total,
                "contratados": contr,
                "conversion_pct": pct,
            }
        )
    return jsonify(out)


@dashboard_bp.route("/dashboard/api/tiempo-etapa")
@login_required
def api_tiempo_etapa():
    """
    Promedio de horas entre entradas consecutivas del historial por estado destino.
    Aproximación de tiempo en etapa cuando el historial registra cambios de estado.
    """
    if not current_user.puede_ver_seleccion:
        return jsonify({"error": "Sin permiso."}), 403

    app_ids = (
        db.session.query(HistorialProceso.id_aplicacion)
        .filter(HistorialProceso.id_aplicacion.isnot(None))
        .distinct()
        .all()
    )
    sums = defaultdict(float)
    counts = defaultdict(int)
    for (app_id,) in app_ids:
        hist = (
            HistorialProceso.query.filter_by(id_aplicacion=app_id)
            .order_by(HistorialProceso.fecha_accion.asc(), HistorialProceso.id.asc())
            .all()
        )
        for i in range(1, len(hist)):
            h_prev, h = hist[i - 1], hist[i]
            if h.estado_nuevo:
                delta = (h.fecha_accion - h_prev.fecha_accion).total_seconds()
                if delta >= 0:
                    sums[h.estado_nuevo] += delta
                    counts[h.estado_nuevo] += 1
    data = []
    for codigo in sorted(sums.keys(), key=lambda c: counts.get(c, 0), reverse=True):
        if counts[codigo]:
            horas = round(sums[codigo] / counts[codigo] / 3600, 2)
            data.append(
                {
                    "estado": codigo,
                    "nombre": ESTADOS_DICT.get(codigo, codigo),
                    "horas_promedio": horas,
                    "muestras": counts[codigo],
                }
            )
    return jsonify(data)


@dashboard_bp.route("/dashboard/api/sesgos")
@login_required
def api_sesgos():
    """Heurística simple: concentración de rechazos por ciudad."""
    if not current_user.es_admin:
        return jsonify({"error": "Solo administración."}), 403

    rows = (
        db.session.query(Candidato.ciudad, func.count(Aplicacion.id))
        .join(Aplicacion, Candidato.cedula == Aplicacion.cedula_candidato)
        .filter(
            Aplicacion.estado == "rechazado",
            Candidato.ciudad.isnot(None),
            Candidato.ciudad != "",
        )
        .group_by(Candidato.ciudad)
        .order_by(func.count(Aplicacion.id).desc())
        .limit(12)
        .all()
    )
    total_rech = Aplicacion.query.filter_by(estado="rechazado").count()
    lista = [{"ciudad": c or "—", "rechazos": int(n)} for c, n in rows]
    alertas = []
    if total_rech >= 8 and lista:
        top = lista[0]
        ratio = top["rechazos"] / total_rech
        if ratio >= 0.45:
            alertas.append(
                {
                    "tipo": "rechazos_por_ciudad",
                    "mensaje": f'Más del 45% de rechazos concentrados en «{top["ciudad"]}» ({top["rechazos"]}/{total_rech}). Revisar sesgo posible.',
                    "ratio": round(ratio, 2),
                }
            )
    return jsonify({"total_rechazos": total_rech, "por_ciudad": lista, "alertas": alertas})


@reportes_bp.route("/")
@login_required
def index():
    if not current_user.puede_ver_seleccion:
        flash("Sin permisos para reportes.", "danger")
        return redirect(url_for("dashboard.index"))

    corte = datetime.utcnow() - timedelta(days=30)
    rep_kpis = {
        "candidatos_activos": Candidato.query.filter_by(activo=True).count(),
        "vacantes_abiertas": Vacante.query.filter_by(estado="abierta").count(),
        "postulaciones_30d": Aplicacion.query.filter(
            Aplicacion.fecha_aplicacion.isnot(None), Aplicacion.fecha_aplicacion >= corte
        ).count(),
    }
    return render_template("reportes/index.html", rep_kpis=rep_kpis)


@reportes_bp.route("/auditoria-seleccion")
@login_required
def auditoria_seleccion():
    if not current_user.es_rrhh:
        flash("Solo RRHH o administración.", "danger")
        return redirect(url_for("reportes.index"))
    lim = min(500, request.args.get("lim", default=200, type=int))
    rows = HistorialProceso.query.order_by(HistorialProceso.id.desc()).limit(lim).all()
    return render_template("reportes/auditoria_seleccion.html", rows=rows, lim=lim)


@reportes_bp.route("/auditoria-seleccion/exportar")
@login_required
def exportar_auditoria_seleccion():
    if not current_user.es_rrhh:
        return redirect(url_for("reportes.index"))
    lim = min(10000, request.args.get("lim", default=5000, type=int))
    rows = HistorialProceso.query.order_by(HistorialProceso.id.desc()).limit(lim).all()
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["id", "fecha", "cedula", "id_aplicacion", "accion", "estado_ant", "estado_nuevo", "observaciones", "id_usuario"])
    for r in rows:
        w.writerow(
            [
                r.id,
                r.fecha_accion.strftime("%Y-%m-%d %H:%M:%S") if r.fecha_accion else "",
                r.cedula_candidato or "",
                r.id_aplicacion or "",
                r.accion or "",
                r.estado_anterior or "",
                r.estado_nuevo or "",
                (r.observaciones or "")[:800],
                r.id_usuario or "",
            ]
        )
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=auditoria_seleccion.csv"},
    )


@reportes_bp.route("/exportar-candidatos")
@login_required
def exportar_candidatos():
    """Exporta candidatos activos a CSV (respeta filtros opcionales q, estado, ciudad)."""
    if not current_user.puede_ver_seleccion:
        return redirect(url_for("reportes.index"))

    from sqlalchemy import exists as sa_exists

    qf = (request.args.get("q") or "").strip()
    estado = (request.args.get("estado") or "").strip()
    ciudad = (request.args.get("ciudad") or "").strip()

    query = Candidato.query.filter_by(activo=True)
    if qf:
        like = f"%{qf}%"
        query = query.filter(
            db.or_(
                Candidato.cedula.ilike(like),
                Candidato.nombres.ilike(like),
                Candidato.apellidos.ilike(like),
                Candidato.correo.ilike(like),
            )
        )
    if ciudad:
        query = query.filter(Candidato.ciudad.ilike(f"%{ciudad}%"))
    if estado:
        query = query.filter(
            sa_exists().where(
                Aplicacion.cedula_candidato == Candidato.cedula,
                Aplicacion.estado == estado,
            )
        )

    candidatos = query.order_by(Candidato.fecha_registro.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Cédula", "Nombres", "Apellidos", "Teléfono", "Correo",
        "Ciudad", "Fuente", "Fecha Registro", "Estado Actual"
    ])

    for c in candidatos:
        writer.writerow([
            c.cedula, c.nombres, c.apellidos, c.telefono, c.correo,
            c.ciudad, c.fuente_captacion,
            c.fecha_registro.strftime("%Y-%m-%d") if c.fecha_registro else "",
            c.ultimo_estado,
        ])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=candidatos_talentflow.csv"},
    )


@reportes_bp.route("/exportar-empleados")
@login_required
def exportar_empleados():
    if not current_user.es_rrhh:
        return redirect(url_for("reportes.index"))

    empleados = Empleado.query.order_by(Empleado.fecha_ingreso.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ID Empleado",
            "Cedula",
            "Nombre",
            "Estado Laboral",
            "Cargo Actual",
            "Sede Actual",
            "Fecha Ingreso",
            "Fecha Salida",
            "Motivo Salida",
        ]
    )
    for emp in empleados:
        actual = next((a for a in emp.asignaciones if a.es_actual), None)
        writer.writerow(
            [
                emp.id,
                emp.cedula,
                emp.candidato.nombre_completo if emp.candidato else emp.cedula,
                emp.estado_laboral,
                actual.cargo.nombre if actual and actual.cargo else "",
                actual.sede.nombre if actual and actual.sede else "",
                emp.fecha_ingreso.isoformat() if emp.fecha_ingreso else "",
                emp.fecha_salida.isoformat() if emp.fecha_salida else "",
                emp.motivo_salida or "",
            ]
        )
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=empleados_hr.csv"},
    )


@reportes_bp.route("/exportar-evaluaciones-desempeno")
@login_required
def exportar_evaluaciones_desempeno():
    if not current_user.es_rrhh:
        return redirect(url_for("reportes.index"))

    rows = (
        db.session.query(
            EvaluacionDesempeno,
            Empleado,
            Cargo.nombre.label("cargo_nombre"),
            Sede.nombre.label("sede_nombre"),
        )
        .join(Empleado, Empleado.id == EvaluacionDesempeno.id_empleado)
        .outerjoin(AsignacionLaboral, db.and_(AsignacionLaboral.id_empleado == Empleado.id, AsignacionLaboral.es_actual.is_(True)))
        .outerjoin(Cargo, Cargo.id == AsignacionLaboral.id_cargo)
        .outerjoin(Sede, Sede.id == AsignacionLaboral.id_sede)
        .order_by(EvaluacionDesempeno.fecha_registro.desc())
        .all()
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Evaluacion ID",
            "Periodo",
            "Cedula",
            "Empleado",
            "Cargo",
            "Sede",
            "Puntaje",
            "Estado Aceptacion",
            "Fecha Evaluacion",
        ]
    )
    for ev, emp, cargo_nombre, sede_nombre in rows:
        writer.writerow(
            [
                ev.id,
                ev.periodo,
                emp.cedula,
                emp.candidato.nombre_completo if emp.candidato else emp.cedula,
                cargo_nombre or "",
                sede_nombre or "",
                ev.puntaje_total or 0,
                ev.estado_aceptacion,
                ev.fecha_evaluacion.isoformat() if ev.fecha_evaluacion else "",
            ]
        )
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=evaluaciones_desempeno.csv"},
    )


@reportes_bp.route("/exportar-integracion-ats")
@login_required
def exportar_integracion_ats():
    """CSV plano para integraciones externas (ATS / nómina): una fila por postulación."""
    if not (current_user.es_rrhh or current_user.es_reclutador):
        flash("Sin permisos.", "danger")
        return redirect(url_for("reportes.index"))

    lim = min(10000, request.args.get("lim", default=5000, type=int))
    rows = (
        db.session.query(Aplicacion, Candidato, Vacante)
        .join(Candidato, Candidato.cedula == Aplicacion.cedula_candidato)
        .join(Vacante, Vacante.id == Aplicacion.id_vacante)
        .order_by(Aplicacion.fecha_aplicacion.desc())
        .limit(lim)
        .all()
    )
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(
        [
            "id_aplicacion",
            "cedula_candidato",
            "nombres",
            "apellidos",
            "email_candidato",
            "telefono",
            "ciudad_candidato",
            "id_vacante",
            "titulo_vacante",
            "estado_postulacion",
            "fecha_aplicacion",
            "score",
        ]
    )
    for ap, cand, vac in rows:
        w.writerow(
            [
                ap.id,
                cand.cedula,
                cand.nombres,
                cand.apellidos,
                cand.correo,
                cand.telefono or "",
                cand.ciudad or "",
                vac.id,
                vac.titulo,
                ap.estado or "",
                ap.fecha_aplicacion.strftime("%Y-%m-%d %H:%M:%S") if ap.fecha_aplicacion else "",
                ap.score if ap.score is not None else "",
            ]
        )
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=talentflow_export_ats.csv"},
    )
