"""
TalentFlow — Controlador de Vacantes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Vacante, Aplicacion, ESTADOS_APLICACION
from extensions import db

vacantes_bp = Blueprint("vacantes", __name__, url_prefix="/vacantes")


@vacantes_bp.route("/")
@login_required
def lista():
    estado = request.args.get("estado", "")
    query = Vacante.query
    if estado:
        query = query.filter_by(estado=estado)
    vacantes = query.order_by(Vacante.fecha_creacion.desc()).all()
    return render_template("vacantes/lista.html", vacantes=vacantes, filtro_estado=estado)


@vacantes_bp.route("/nueva", methods=["GET", "POST"])
@login_required
def nueva():
    if not current_user.es_reclutador:
        flash("Sin permisos.", "danger")
        return redirect(url_for("vacantes.lista"))

    if request.method == "POST":
        vacante = Vacante(
            titulo=request.form.get("titulo", "").strip(),
            descripcion=request.form.get("descripcion", "").strip(),
            area=request.form.get("area", "").strip(),
            ciudad=request.form.get("ciudad", "").strip(),
            tipo_contrato=request.form.get("tipo_contrato", "").strip(),
            requisitos=request.form.get("requisitos", "").strip(),
            id_responsable=current_user.id,
        )
        sal_min = request.form.get("salario_min")
        sal_max = request.form.get("salario_max")
        if sal_min:
            vacante.salario_min = float(sal_min)
        if sal_max:
            vacante.salario_max = float(sal_max)

        db.session.add(vacante)
        db.session.commit()
        flash(f"Vacante '{vacante.titulo}' creada.", "success")
        return redirect(url_for("vacantes.detalle", vid=vacante.id))

    return render_template("vacantes/formulario.html")


@vacantes_bp.route("/<int:vid>")
@login_required
def detalle(vid):
    vacante = Vacante.query.get_or_404(vid)
    return render_template("vacantes/detalle.html", vacante=vacante, estados=ESTADOS_APLICACION)


@vacantes_bp.route("/<int:vid>/cerrar", methods=["POST"])
@login_required
def cerrar(vid):
    if not current_user.es_admin:
        flash("Sin permisos.", "danger")
        return redirect(url_for("vacantes.detalle", vid=vid))
    v = Vacante.query.get_or_404(vid)
    v.estado = "cerrada"
    db.session.commit()
    flash("Vacante cerrada.", "info")
    return redirect(url_for("vacantes.lista"))
