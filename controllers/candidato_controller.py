"""
TalentFlow — Controlador de Candidatos
CRUD completo, carga de documentos y búsqueda avanzada.
"""

import os
import tempfile
import uuid
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
    send_from_directory,
    abort,
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import exists

from models import (
    Aplicacion,
    Candidato,
    DocumentoAdjunto,
    Empleado,
    ESTADOS_APLICACION,
    HistorialProceso,
    HojaDeVida,
    Vacante,
)
from extensions import db

candidatos_bp = Blueprint("candidatos", __name__, url_prefix="/candidatos")

EXTENSIONES_PERMITIDAS = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}


def extension_permitida(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in EXTENSIONES_PERMITIDAS


# ─── Lista y búsqueda ──────────────────────────────────────────────────────────

@candidatos_bp.route("/")
@login_required
def lista():
    if not current_user.puede_ver_seleccion:
        flash("No tiene permisos para ver candidatos.", "danger")
        return redirect(url_for("dashboard.index"))

    q = request.args.get("q", "").strip()
    estado = request.args.get("estado", "")
    ciudad = request.args.get("ciudad", "")
    page = max(1, request.args.get("page", default=1, type=int))
    per_page = 15

    query = Candidato.query.filter_by(activo=True)

    if q:
        like = f"%{q}%"
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
            exists().where(
                Aplicacion.cedula_candidato == Candidato.cedula,
                Aplicacion.estado == estado,
            )
        )

    pagination = query.order_by(Candidato.fecha_registro.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    for c in pagination.items:
        apps = sorted(
            c.aplicaciones,
            key=lambda x: x.fecha_aplicacion or datetime.min,
            reverse=True,
        )
        c._ultima_aplicacion = apps[0] if apps else None

    return render_template(
        "candidatos/lista.html",
        candidatos=pagination.items,
        pagination=pagination,
        estados=ESTADOS_APLICACION,
        filtro_q=q,
        filtro_estado=estado,
        filtro_ciudad=ciudad,
    )


@candidatos_bp.route("/bulk-estado", methods=["POST"])
@login_required
def bulk_estado_aplicaciones():
    """Cambio de estado masivo para aplicaciones seleccionadas (última postulación en listado)."""
    if not current_user.es_reclutador:
        flash("Sin permisos para cambiar estados.", "danger")
        return redirect(url_for("candidatos.lista"))

    raw_ids = request.form.getlist("app_ids")
    nuevo_estado = (request.form.get("nuevo_estado") or "").strip()
    estados_validos = [e[0] for e in ESTADOS_APLICACION]
    if not raw_ids or nuevo_estado not in estados_validos:
        flash("Selecciona al menos una aplicación y un estado válido.", "warning")
        return redirect(url_for("candidatos.lista"))

    from services.hr_lifecycle import asegurar_empleado_por_contratacion

    def _reg_hist(aplicacion, accion, estado_ant, estado_nuevo, obs=None):
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

    n = 0
    for sid in raw_ids:
        try:
            aid = int(sid)
        except (TypeError, ValueError):
            continue
        aplicacion = db.session.get(Aplicacion, aid)
        if not aplicacion:
            continue
        estado_ant = aplicacion.estado
        if estado_ant == nuevo_estado:
            continue
        aplicacion.estado = nuevo_estado
        _reg_hist(
            aplicacion,
            f"Cambio masivo de estado: {estado_ant} → {nuevo_estado}",
            estado_ant,
            nuevo_estado,
            request.form.get("observaciones", "")[:500],
        )
        if nuevo_estado == "contratado" and estado_ant != "contratado":
            asegurar_empleado_por_contratacion(aplicacion, current_user.id)
        n += 1
    db.session.commit()

    flash(f"Actualizadas {n} aplicación(es).", "success" if n else "info")
    return redirect(url_for("candidatos.lista"))


# ─── Crear candidato ──────────────────────────────────────────────────────────

@candidatos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    if not current_user.es_reclutador:
        flash("No tienes permisos para registrar candidatos.", "danger")
        return redirect(url_for("candidatos.lista"))

    if request.method == "POST":
        cedula = request.form.get("cedula", "").strip()

        if db.session.get(Candidato, cedula):
            flash(f"Ya existe un candidato con la cédula {cedula}.", "warning")
            return redirect(url_for("candidatos.detalle", cedula=cedula))

        candidato = Candidato(
            cedula=cedula,
            nombres=request.form.get("nombres", "").strip(),
            apellidos=request.form.get("apellidos", "").strip(),
            telefono=request.form.get("telefono", "").strip(),
            correo=request.form.get("correo", "").strip().lower(),
            direccion=request.form.get("direccion", "").strip(),
            ciudad=request.form.get("ciudad", "").strip(),
            fuente_captacion=request.form.get("fuente_captacion", "").strip(),
        )
        db.session.add(candidato)

        # Hoja de vida básica
        habilidades_raw = request.form.get("habilidades", "")
        habilidades = [h.strip() for h in habilidades_raw.split(",") if h.strip()]

        hdv = HojaDeVida(
            cedula_candidato=cedula,
            resumen_profesional=request.form.get("resumen_profesional", ""),
            habilidades=habilidades,
            experiencia_laboral=[],
            formacion_academica=[],
        )
        db.session.add(hdv)
        db.session.flush()

        # Registrar en historial
        registro = HistorialProceso(
            cedula_candidato=cedula,
            id_usuario=current_user.id,
            accion="Candidato registrado en el sistema",
        )
        db.session.add(registro)
        db.session.commit()

        # Subir archivo PDF si viene en el form
        archivo = request.files.get("archivo_hv")
        if archivo and archivo.filename and extension_permitida(archivo.filename):
            _guardar_documento(archivo, cedula, "hoja_de_vida", None)

        flash(f"Candidato {candidato.nombre_completo} registrado exitosamente.", "success")
        return redirect(url_for("candidatos.detalle", cedula=cedula))

    vacantes = Vacante.query.filter_by(estado="abierta").all()
    return render_template("candidatos/formulario.html", vacantes=vacantes)


# ─── Detalle de candidato ─────────────────────────────────────────────────────

@candidatos_bp.route("/<cedula>")
@login_required
def detalle(cedula):
    if not current_user.puede_ver_seleccion:
        flash("No tiene permisos para ver candidatos.", "danger")
        return redirect(url_for("dashboard.index"))

    candidato = Candidato.query.get_or_404(cedula)
    vacantes = Vacante.query.filter_by(estado="abierta").all()
    return render_template(
        "candidatos/detalle.html",
        candidato=candidato,
        vacantes=vacantes,
        estados=ESTADOS_APLICACION,
    )


@candidatos_bp.route("/<cedula>/expediente")
@login_required
def expediente(cedula):
    if not current_user.puede_ver_seleccion:
        flash("No tiene permisos para ver expedientes.", "danger")
        return redirect(url_for("dashboard.index"))

    candidato = Candidato.query.get_or_404(cedula)
    documentos = sorted(
        candidato.documentos,
        key=lambda d: d.fecha_subida or datetime.min,
        reverse=True,
    )
    return render_template(
        "candidatos/expediente.html",
        candidato=candidato,
        documentos=documentos,
    )


# ─── Editar candidato ─────────────────────────────────────────────────────────

@candidatos_bp.route("/<cedula>/editar", methods=["GET", "POST"])
@login_required
def editar(cedula):
    if not current_user.es_reclutador:
        flash("Sin permisos.", "danger")
        return redirect(url_for("candidatos.detalle", cedula=cedula))

    candidato = Candidato.query.get_or_404(cedula)

    if request.method == "POST":
        candidato.nombres = request.form.get("nombres", "").strip()
        candidato.apellidos = request.form.get("apellidos", "").strip()
        candidato.telefono = request.form.get("telefono", "").strip()
        candidato.correo = request.form.get("correo", "").strip().lower()
        candidato.direccion = request.form.get("direccion", "").strip()
        candidato.ciudad = request.form.get("ciudad", "").strip()

        if candidato.hoja_de_vida:
            hdv = candidato.hoja_de_vida
        else:
            hdv = HojaDeVida(cedula_candidato=cedula)
            db.session.add(hdv)

        habilidades_raw = request.form.get("habilidades", "")
        hdv.habilidades = [h.strip() for h in habilidades_raw.split(",") if h.strip()]
        hdv.resumen_profesional = request.form.get("resumen_profesional", "")

        db.session.commit()
        flash("Información actualizada.", "success")
        return redirect(url_for("candidatos.detalle", cedula=cedula))

    return render_template("candidatos/formulario.html", candidato=candidato, editando=True)


# ─── Subir documento ─────────────────────────────────────────────────────────

@candidatos_bp.route("/<cedula>/documentos", methods=["POST"])
@login_required
def subir_documento(cedula):
    if not current_user.es_reclutador:
        flash("Sin permisos.", "danger")
        return redirect(url_for("candidatos.detalle", cedula=cedula))

    candidato = Candidato.query.get_or_404(cedula)
    archivo = request.files.get("archivo")
    tipo = request.form.get("tipo_documento", "documento")
    id_aplicacion = request.form.get("id_aplicacion")

    if not archivo or not archivo.filename:
        flash("Selecciona un archivo.", "warning")
        return redirect(url_for("candidatos.detalle", cedula=cedula))

    if not extension_permitida(archivo.filename):
        flash("Tipo de archivo no permitido. Solo PDF, DOC, DOCX, JPG, PNG.", "danger")
        return redirect(url_for("candidatos.detalle", cedula=cedula))

    _guardar_documento(archivo, cedula, tipo, id_aplicacion)
    flash("Documento cargado exitosamente.", "success")
    return redirect(url_for("candidatos.detalle", cedula=cedula))


@candidatos_bp.route("/<cedula>/sugerir-desde-cv", methods=["POST"])
@login_required
def sugerir_desde_cv(cedula):
    if not current_user.es_reclutador:
        flash("Sin permisos.", "danger")
        return redirect(url_for("candidatos.detalle", cedula=cedula))
    candidato = Candidato.query.get_or_404(cedula)
    archivo = request.files.get("archivo_cv")
    if not archivo or not archivo.filename:
        flash("Selecciona un archivo PDF.", "warning")
        return redirect(url_for("candidatos.detalle", cedula=cedula))
    if not archivo.filename.lower().endswith(".pdf"):
        flash("Por ahora solo se analizan PDF.", "warning")
        return redirect(url_for("candidatos.detalle", cedula=cedula))
    fd, tmp = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    try:
        archivo.save(tmp)
        from services.cv_parser import extract_text_from_pdf, suggest_fields_from_text

        text = extract_text_from_pdf(tmp)
        sug = suggest_fields_from_text(text)
        correos = ", ".join(sug.get("correos") or []) or "—"
        tels = ", ".join(sug.get("telefonos") or []) or "—"
        frag = (sug.get("fragmento") or "")[:400].replace("\n", " ")
        flash(
            f"Extracción CV (revísalo antes de guardar): correos [{correos}] · "
            f"tel [{tels}] · extracto: {frag}",
            "info",
        )
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    return redirect(url_for("candidatos.editar", cedula=cedula))


def _guardar_documento(archivo, cedula, tipo, id_aplicacion):
    """Guarda el archivo en disco y registra en BD."""
    ext = archivo.filename.rsplit(".", 1)[1].lower()
    nombre_uuid = f"{uuid.uuid4().hex}.{ext}"
    carpeta = os.path.join(current_app.config["UPLOAD_FOLDER"], cedula, tipo)
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, nombre_uuid)
    archivo.save(ruta)

    doc = DocumentoAdjunto(
        cedula_candidato=cedula,
        id_aplicacion=int(id_aplicacion) if id_aplicacion else None,
        tipo_documento=tipo,
        nombre_original=secure_filename(archivo.filename),
        nombre_archivo=nombre_uuid,
        ruta_archivo=ruta,
        tamano_bytes=os.path.getsize(ruta),
        subido_por=current_user.id,
    )
    db.session.add(doc)
    db.session.commit()


# ─── Descargar / vista previa documento ─────────────────────────────────────

_PREVIEW_MIMETYPES = {
    "pdf": "application/pdf",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "webp": "image/webp",
}


def _puede_acceder_documento(doc: DocumentoAdjunto) -> bool:
    if not current_user.is_authenticated:
        return False
    if current_user.puede_ver_seleccion:
        return True
    emp = Empleado.query.filter_by(cedula=doc.cedula_candidato).first()
    return bool(emp and emp.id_usuario == current_user.id)


@candidatos_bp.route("/documentos/<int:doc_id>/descargar")
@login_required
def descargar_documento(doc_id):
    doc = db.session.get(DocumentoAdjunto, doc_id)
    if not doc:
        abort(404)
    if not _puede_acceder_documento(doc):
        abort(403)
    carpeta = os.path.dirname(doc.ruta_archivo)
    return send_from_directory(
        carpeta,
        doc.nombre_archivo,
        as_attachment=True,
        download_name=doc.nombre_original,
    )


@candidatos_bp.route("/documentos/<int:doc_id>/ver")
@login_required
def visualizar_documento(doc_id):
    doc = db.session.get(DocumentoAdjunto, doc_id)
    if not doc:
        abort(404)
    if not _puede_acceder_documento(doc):
        abort(403)
    ext = (doc.nombre_archivo or "").rsplit(".", 1)[-1].lower()
    mimetype = _PREVIEW_MIMETYPES.get(ext)
    if not mimetype:
        flash("Este tipo de archivo no tiene vista previa en el navegador. Usa descargar.", "info")
        return redirect(url_for("candidatos.descargar_documento", doc_id=doc.id))
    carpeta = os.path.dirname(doc.ruta_archivo)
    resp = send_from_directory(
        carpeta,
        doc.nombre_archivo,
        as_attachment=False,
        mimetype=mimetype,
        download_name=doc.nombre_original,
    )
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp


# ─── Aplicar a vacante ────────────────────────────────────────────────────────

@candidatos_bp.route("/<cedula>/aplicar", methods=["POST"])
@login_required
def aplicar_vacante(cedula):
    if not current_user.es_reclutador:
        flash("Sin permisos.", "danger")
        return redirect(url_for("candidatos.detalle", cedula=cedula))

    candidato = Candidato.query.get_or_404(cedula)
    try:
        id_vacante = int(request.form.get("id_vacante", ""))
    except (TypeError, ValueError):
        flash("Vacante no válida.", "danger")
        return redirect(url_for("candidatos.detalle", cedula=cedula))

    if not db.session.get(Vacante, id_vacante):
        flash("Vacante no encontrada.", "danger")
        return redirect(url_for("candidatos.detalle", cedula=cedula))

    existente = Aplicacion.query.filter_by(
        cedula_candidato=cedula, id_vacante=id_vacante
    ).first()
    if existente:
        flash("El candidato ya está aplicado a esta vacante.", "warning")
        return redirect(url_for("candidatos.detalle", cedula=cedula))

    aplicacion = Aplicacion(
        cedula_candidato=cedula,
        id_vacante=id_vacante,
        estado="hoja_de_vida_recibida",
    )
    db.session.add(aplicacion)
    db.session.flush()

    try:
        from services.scoring import calcular_score_aplicacion

        sc = calcular_score_aplicacion(aplicacion)
        if sc is not None:
            aplicacion.score = sc
    except Exception:
        pass

    historial = HistorialProceso(
        cedula_candidato=cedula,
        id_aplicacion=aplicacion.id,
        id_usuario=current_user.id,
        accion="Aplicación creada",
        estado_nuevo="hoja_de_vida_recibida",
    )
    db.session.add(historial)
    db.session.commit()
    flash("Candidato aplicado a la vacante.", "success")
    return redirect(url_for("candidatos.detalle", cedula=cedula))
