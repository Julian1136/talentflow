"""
TalentFlow — Controlador del Proceso de Selección
Contactos, entrevistas, evaluaciones psicológicas y técnicas, cambio de estado.
"""

import json
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from models import (
    Aplicacion,
    Contacto,
    Entrevista,
    EvaluacionPsicologica,
    EvaluacionPlantillaRespuesta,
    EvaluacionTecnica,
    HistorialProceso,
    NotaInternaAplicacion,
    PlantillaEvaluacion,
    ESTADOS_APLICACION,
    Usuario,
)
from extensions import db
from services.hr_lifecycle import asegurar_empleado_por_contratacion

proceso_bp = Blueprint("proceso", __name__, url_prefix="/proceso")


def _puede_evaluacion_plantilla() -> bool:
    r = getattr(current_user, "rol", None)
    nombre = r.nombre if r else ""
    return nombre in ("administrador", "reclutador", "jefe_area")


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


# ─── Vista principal del proceso ──────────────────────────────────────────────

@proceso_bp.route("/<int:app_id>")
@login_required
def detalle(app_id):
    if not current_user.puede_ver_seleccion:
        flash("No tiene permisos para ver el proceso de selección.", "danger")
        return redirect(url_for("dashboard.index"))

    aplicacion = db.session.get(Aplicacion, app_id)
    if not aplicacion:
        abort(404)
    usuarios = Usuario.query.filter_by(activo=True).all()
    now_local = datetime.now().strftime("%Y-%m-%dT%H:%M")
    plantillas = (
        PlantillaEvaluacion.query.filter_by(activa=True)
        .order_by(PlantillaEvaluacion.nombre)
        .all()
    )
    plantillas_data = []
    for p in plantillas:
        try:
            crit = json.loads(p.criterios_json)
        except (json.JSONDecodeError, TypeError):
            crit = []
        plantillas_data.append({"id": p.id, "nombre": p.nombre, "criterios": crit})
    historial_proceso = sorted(
        aplicacion.historial,
        key=lambda h: (h.fecha_accion or datetime.min, h.id),
        reverse=True,
    )
    notas_internas = list(aplicacion.notas_internas)

    return render_template(
        "proceso/detalle.html",
        aplicacion=aplicacion,
        estados=ESTADOS_APLICACION,
        usuarios=usuarios,
        now_local=now_local,
        plantillas_data=plantillas_data,
        puede_plantilla_eval=_puede_evaluacion_plantilla(),
        historial_proceso=historial_proceso,
        notas_internas=notas_internas,
    )


@proceso_bp.route("/<int:app_id>/nota-interna", methods=["POST"])
@login_required
def agregar_nota_interna(app_id):
    if not current_user.es_reclutador:
        flash("Sin permisos para notas internas.", "danger")
        return redirect(url_for("proceso.detalle", app_id=app_id))
    aplicacion = db.session.get(Aplicacion, app_id)
    if not aplicacion:
        abort(404)
    cuerpo = (request.form.get("cuerpo") or "").strip()
    if not cuerpo:
        flash("Escribe el contenido de la nota.", "warning")
        return redirect(url_for("proceso.detalle", app_id=app_id))
    db.session.add(
        NotaInternaAplicacion(
            id_aplicacion=aplicacion.id,
            id_usuario=current_user.id,
            cuerpo=cuerpo[:8000],
        )
    )
    db.session.commit()
    flash("Nota interna registrada.", "success")
    return redirect(url_for("proceso.detalle", app_id=app_id))


# ─── Cambiar estado ───────────────────────────────────────────────────────────

@proceso_bp.route("/<int:app_id>/estado", methods=["POST"])
@login_required
def cambiar_estado(app_id):
    if not current_user.es_reclutador:
        if request.is_json:
            return jsonify({"ok": False, "error": "Sin permisos."}), 403
        flash("Sin permisos.", "danger")
        return redirect(url_for("proceso.detalle", app_id=app_id))
 
    aplicacion = db.session.get(Aplicacion, app_id)   # ← corregido: .get() moderno
    if not aplicacion:
        abort(404)
 
    # Soportar tanto form-data (vista detalle) como JSON (Kanban)
    if request.is_json:
        data = request.get_json(silent=True) or {}
        nuevo_estado   = data.get("estado", "").strip()
        observaciones  = data.get("observaciones", "")
    else:
        nuevo_estado   = request.form.get("estado", "").strip()
        observaciones  = request.form.get("observaciones", "")
 
    estados_validos = [e[0] for e in ESTADOS_APLICACION]
    if nuevo_estado not in estados_validos:
        if request.is_json:
            return jsonify({"ok": False, "error": "Estado no válido."}), 400
        flash("Estado no válido.", "danger")
        return redirect(url_for("proceso.detalle", app_id=app_id))
 
    estado_anterior = aplicacion.estado
    aplicacion.estado = nuevo_estado
    _registrar_historial(
        aplicacion,
        accion=f"Estado cambiado: {estado_anterior} → {nuevo_estado}",
        estado_ant=estado_anterior,
        estado_nuevo=nuevo_estado,
        obs=observaciones,
    )
    if nuevo_estado == "contratado" and estado_anterior != "contratado":
        asegurar_empleado_por_contratacion(aplicacion, current_user.id)
    db.session.commit()

    try:
        from services.email_service import notificar_cambio_estado

        notificar_cambio_estado(aplicacion, estado_anterior, nuevo_estado)
    except Exception:
        pass

    if request.is_json:
        return jsonify({
            "ok": True,
            "estado_legible": aplicacion.estado_legible,
            "estado_codigo": nuevo_estado,
        })

    flash(f"Estado actualizado a: {aplicacion.estado_legible}", "success")
    return redirect(url_for("proceso.detalle", app_id=app_id))


# ─── Registrar contacto ───────────────────────────────────────────────────────

@proceso_bp.route("/<int:app_id>/contacto", methods=["POST"])
@login_required
def registrar_contacto(app_id):
    aplicacion = Aplicacion.query.get_or_404(app_id)

    fecha_str = request.form.get("fecha_contacto")
    fecha = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M") if fecha_str else datetime.utcnow()

    contacto = Contacto(
        cedula_candidato=aplicacion.cedula_candidato,
        id_aplicacion=app_id,
        id_usuario=current_user.id,
        fecha_contacto=fecha,
        canal=request.form.get("canal"),
        resultado=request.form.get("resultado"),
        observaciones=request.form.get("observaciones"),
    )
    db.session.add(contacto)

    if aplicacion.estado == "hoja_de_vida_recibida":
        aplicacion.estado = "contactado"
        _registrar_historial(aplicacion, "Contacto registrado", "hoja_de_vida_recibida", "contactado")

    _registrar_historial(aplicacion, f"Contacto vía {contacto.canal}: {contacto.resultado}")
    db.session.commit()
    flash("Contacto registrado.", "success")
    return redirect(url_for("proceso.detalle", app_id=app_id))


# ─── Programar entrevista ─────────────────────────────────────────────────────

@proceso_bp.route("/<int:app_id>/entrevista", methods=["POST"])
@login_required
def programar_entrevista(app_id):
    if not current_user.es_reclutador:
        flash("Sin permisos.", "danger")
        return redirect(url_for("proceso.detalle", app_id=app_id))

    aplicacion = Aplicacion.query.get_or_404(app_id)
    fecha_str = request.form.get("fecha_programada")
    fecha = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M") if fecha_str else None

    entrevista = Entrevista(
        id_aplicacion=app_id,
        tipo=request.form.get("tipo"),
        fecha_programada=fecha,
        lugar=request.form.get("lugar"),
        id_entrevistador=request.form.get("id_entrevistador") or current_user.id,
        resultado="pendiente",
    )
    db.session.add(entrevista)

    estado_ant = aplicacion.estado
    aplicacion.estado = "entrevista_programada"
    _registrar_historial(
        aplicacion, "Entrevista programada",
        estado_ant, "entrevista_programada",
        obs=f"Tipo: {entrevista.tipo}, Lugar: {entrevista.lugar}",
    )
    db.session.commit()

    try:
        from services.email_service import notificar_entrevista_programada

        enviado = notificar_entrevista_programada(entrevista)
        if enviado:
            flash(
                "Entrevista programada. Correo de citación enviado al candidato.",
                "success",
            )
        else:
            flash("Entrevista programada.", "success")
    except Exception:
        flash("Entrevista programada.", "success")

    return redirect(url_for("proceso.detalle", app_id=aplicacion.id))


# ─── Registrar resultado de entrevista ────────────────────────────────────────

@proceso_bp.route("/entrevista/<int:ent_id>/resultado", methods=["POST"])
@login_required
def resultado_entrevista(ent_id):
    entrevista = Entrevista.query.get_or_404(ent_id)
    entrevista.resultado = request.form.get("resultado")
    entrevista.observaciones = request.form.get("observaciones")
    entrevista.fecha_realizada = datetime.utcnow()

    aplicacion = entrevista.aplicacion
    estado_ant = aplicacion.estado
    aplicacion.estado = "entrevista_realizada"
    _registrar_historial(
        aplicacion,
        f"Entrevista realizada — resultado: {entrevista.resultado}",
        estado_ant, "entrevista_realizada",
        obs=entrevista.observaciones,
    )
    db.session.commit()
    flash("Resultado de entrevista registrado.", "success")
    return redirect(url_for("proceso.detalle", app_id=aplicacion.id))


@proceso_bp.route("/entrevista/<int:ent_id>/reenviar", methods=["POST"])
@login_required
def reenviar_entrevista(ent_id):
    if not current_user.es_reclutador:
        flash("Sin permisos.", "danger")
        return redirect(url_for("dashboard.index"))

    entrevista = db.session.get(Entrevista, ent_id)
    if not entrevista:
        abort(404)
    if entrevista.resultado == "cancelada":
        flash("La entrevista está cancelada; no se puede reenviar la citación.", "warning")
        return redirect(url_for("proceso.detalle", app_id=entrevista.id_aplicacion))

    enviado = False
    try:
        from services.email_service import notificar_entrevista_programada

        enviado = notificar_entrevista_programada(entrevista)
    except Exception:
        enviado = False

    _registrar_historial(
        entrevista.aplicacion,
        "Citación de entrevista reenviada",
        obs=f"Entrevista #{entrevista.id} ({entrevista.tipo or 'sin tipo'})",
    )
    db.session.commit()

    if enviado:
        flash("Citación reenviada al candidato.", "success")
    else:
        flash("No se pudo enviar el correo; revisa la configuración de email.", "warning")
    return redirect(url_for("proceso.detalle", app_id=entrevista.id_aplicacion))


@proceso_bp.route("/entrevista/<int:ent_id>/cancelar", methods=["POST"])
@login_required
def cancelar_entrevista(ent_id):
    if not current_user.es_reclutador:
        flash("Sin permisos.", "danger")
        return redirect(url_for("dashboard.index"))

    entrevista = db.session.get(Entrevista, ent_id)
    if not entrevista:
        abort(404)
    if entrevista.resultado == "cancelada":
        flash("La entrevista ya estaba cancelada.", "info")
        return redirect(url_for("proceso.detalle", app_id=entrevista.id_aplicacion))

    motivo = (request.form.get("motivo_cancelacion") or "").strip()
    entrevista.resultado = "cancelada"
    entrevista.observaciones = (entrevista.observaciones or "")
    if motivo:
        entrevista.observaciones = (
            (entrevista.observaciones + " | " if entrevista.observaciones else "")
            + f"Cancelación: {motivo}"
        )

    aplicacion = entrevista.aplicacion
    estado_ant = aplicacion.estado
    if estado_ant == "entrevista_programada":
        aplicacion.estado = "contactado"
    _registrar_historial(
        aplicacion,
        "Entrevista cancelada",
        estado_ant=estado_ant,
        estado_nuevo=aplicacion.estado,
        obs=motivo or f"Entrevista #{entrevista.id} cancelada.",
    )

    notificado = False
    try:
        from services.email_service import notificar_entrevista_cancelada

        notificado = notificar_entrevista_cancelada(entrevista, motivo=motivo)
    except Exception:
        notificado = False

    db.session.commit()
    if notificado:
        flash("Entrevista cancelada y candidato notificado.", "warning")
    else:
        flash("Entrevista cancelada.", "warning")
    return redirect(url_for("proceso.detalle", app_id=entrevista.id_aplicacion))


@proceso_bp.route("/entrevista/<int:ent_id>/reprogramar", methods=["POST"])
@login_required
def reprogramar_entrevista(ent_id):
    if not current_user.es_reclutador:
        flash("Sin permisos.", "danger")
        return redirect(url_for("dashboard.index"))

    anterior = db.session.get(Entrevista, ent_id)
    if not anterior:
        abort(404)
    if anterior.resultado == "cancelada":
        flash("No se puede reprogramar una entrevista ya cancelada.", "warning")
        return redirect(url_for("proceso.detalle", app_id=anterior.id_aplicacion))

    fecha_str = request.form.get("fecha_programada")
    if not fecha_str:
        flash("Debes indicar fecha y hora para reprogramar.", "danger")
        return redirect(url_for("proceso.detalle", app_id=anterior.id_aplicacion))
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%dT%H:%M")
    except ValueError:
        flash("Formato de fecha inválido.", "danger")
        return redirect(url_for("proceso.detalle", app_id=anterior.id_aplicacion))

    nuevo_tipo = request.form.get("tipo") or anterior.tipo
    nuevo_lugar = request.form.get("lugar") or anterior.lugar
    nuevo_entrevistador = request.form.get("id_entrevistador", type=int) or anterior.id_entrevistador or current_user.id
    motivo = (request.form.get("motivo_reprogramacion") or "").strip()

    anterior.resultado = "reprogramada"
    anterior.observaciones = (anterior.observaciones or "")
    if motivo:
        anterior.observaciones = (
            (anterior.observaciones + " | " if anterior.observaciones else "")
            + f"Reprogramación: {motivo}"
        )

    nueva = Entrevista(
        id_aplicacion=anterior.id_aplicacion,
        tipo=nuevo_tipo,
        fecha_programada=fecha,
        lugar=nuevo_lugar,
        id_entrevistador=nuevo_entrevistador,
        resultado="pendiente",
    )
    db.session.add(nueva)

    aplicacion = anterior.aplicacion
    estado_ant = aplicacion.estado
    aplicacion.estado = "entrevista_programada"
    _registrar_historial(
        aplicacion,
        "Entrevista reprogramada",
        estado_ant=estado_ant,
        estado_nuevo="entrevista_programada",
        obs=motivo or f"Entrevista #{anterior.id} -> nueva fecha {fecha.strftime('%d/%m/%Y %H:%M')}",
    )

    db.session.commit()

    enviado = False
    try:
        from services.email_service import notificar_entrevista_programada

        enviado = notificar_entrevista_programada(nueva)
    except Exception:
        enviado = False

    if enviado:
        flash("Entrevista reprogramada y citación reenviada.", "success")
    else:
        flash("Entrevista reprogramada.", "success")
    return redirect(url_for("proceso.detalle", app_id=anterior.id_aplicacion))


# ─── Evaluación psicológica ───────────────────────────────────────────────────

@proceso_bp.route("/<int:app_id>/evaluacion-psicologica", methods=["POST"])
@login_required
def registrar_evaluacion_psicologica(app_id):
    if not (current_user.es_psicologo or current_user.es_admin):
        flash("Solo el psicólogo puede registrar esta evaluación.", "danger")
        return redirect(url_for("proceso.detalle", app_id=app_id))

    aplicacion = Aplicacion.query.get_or_404(app_id)
    fecha_str = request.form.get("fecha_evaluacion")
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else None

    ev = EvaluacionPsicologica(
        id_aplicacion=app_id,
        id_psicologo=current_user.id,
        tipo_evaluacion=request.form.get("tipo_evaluacion"),
        fecha_evaluacion=fecha,
        resultado=request.form.get("resultado"),
        observaciones=request.form.get("observaciones"),
        recomendaciones=request.form.get("recomendaciones"),
    )
    db.session.add(ev)

    estado_ant = aplicacion.estado
    aplicacion.estado = "en_pruebas_tecnicas"
    _registrar_historial(
        aplicacion,
        f"Evaluación psicológica registrada — {ev.resultado}",
        estado_ant, "en_pruebas_tecnicas",
    )
    db.session.commit()
    flash("Evaluación psicológica registrada.", "success")
    return redirect(url_for("proceso.detalle", app_id=app_id))


# ─── Prueba técnica ───────────────────────────────────────────────────────────

@proceso_bp.route("/<int:app_id>/prueba-tecnica", methods=["POST"])
@login_required
def registrar_prueba_tecnica(app_id):
    aplicacion = Aplicacion.query.get_or_404(app_id)
    fecha_str = request.form.get("fecha_aplicacion")
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date() if fecha_str else None

    puntaje = request.form.get("puntaje")
    puntaje_max = request.form.get("puntaje_maximo")

    ev = EvaluacionTecnica(
        id_aplicacion=app_id,
        tipo=request.form.get("tipo"),
        nombre_prueba=request.form.get("nombre_prueba"),
        fecha_aplicacion=fecha,
        puntaje=float(puntaje) if puntaje else None,
        puntaje_maximo=float(puntaje_max) if puntaje_max else None,
        resultado=request.form.get("resultado"),
        observaciones=request.form.get("observaciones"),
        id_evaluador=current_user.id,
    )
    db.session.add(ev)
    _registrar_historial(
        aplicacion,
        f"Prueba técnica '{ev.nombre_prueba}' — {ev.resultado}",
    )
    db.session.commit()
    flash("Prueba técnica registrada.", "success")
    return redirect(url_for("proceso.detalle", app_id=app_id))


# ─── Evaluación con plantilla dinámica ────────────────────────────────────────

@proceso_bp.route("/<int:app_id>/evaluacion-plantilla", methods=["POST"])
@login_required
def guardar_evaluacion_plantilla(app_id):
    if not _puede_evaluacion_plantilla():
        flash("Sin permisos para esta evaluación.", "danger")
        return redirect(url_for("proceso.detalle", app_id=app_id))

    aplicacion = Aplicacion.query.get_or_404(app_id)
    pid = request.form.get("id_plantilla", type=int)
    plantilla = db.session.get(PlantillaEvaluacion, pid)
    if not plantilla or not plantilla.activa:
        flash("Plantilla de evaluación no válida.", "danger")
        return redirect(url_for("proceso.detalle", app_id=app_id))

    try:
        criterios = json.loads(plantilla.criterios_json)
    except (json.JSONDecodeError, TypeError):
        flash("La plantilla tiene criterios inválidos.", "danger")
        return redirect(url_for("proceso.detalle", app_id=app_id))

    respuestas = {}
    ponderado = 0.0
    denominador = 0.0
    for c in criterios:
        cid = c.get("id")
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
        respuestas[str(cid)] = val
        ponderado += val * peso
        denominador += max_v * peso

    puntaje = round(100.0 * ponderado / denominador, 2) if denominador > 0 else None

    evr = EvaluacionPlantillaRespuesta(
        id_aplicacion=app_id,
        id_plantilla=plantilla.id,
        id_usuario=current_user.id,
        respuestas_json=json.dumps(respuestas),
        puntaje_total=puntaje,
    )
    db.session.add(evr)
    _registrar_historial(
        aplicacion,
        f"Evaluación con plantilla «{plantilla.nombre}» — puntaje {puntaje if puntaje is not None else '—'}",
    )
    db.session.commit()
    flash("Evaluación con plantilla guardada.", "success")
    return redirect(url_for("proceso.detalle", app_id=app_id))


@proceso_bp.route("/<int:app_id>/compatibilidad-ia", methods=["POST"])
@login_required
def compatibilidad_ia(app_id):
    if not current_user.es_reclutador:
        return jsonify({"ok": False, "error": "Sin permisos."}), 403
    aplicacion = db.session.get(Aplicacion, app_id)
    if not aplicacion:
        return jsonify({"ok": False, "error": "No encontrado."}), 404

    from services.anthropic_match import analizar_compatibilidad

    vac = aplicacion.vacante
    cand = aplicacion.candidato
    hdv = cand.hoja_de_vida
    skills = list(hdv.habilidades) if hdv and hdv.habilidades else []
    resumen = (hdv.resumen_profesional if hdv else None) or ""

    ok, texto = analizar_compatibilidad(
        titulo_vacante=vac.titulo,
        descripcion_vacante=vac.descripcion or vac.requisitos or "",
        resumen_candidato=resumen,
        habilidades=skills,
    )
    if ok:
        aplicacion.analisis_ia_text = texto
        db.session.commit()
        return jsonify({"ok": True, "texto": texto})
    return jsonify({"ok": False, "error": texto}), 200
