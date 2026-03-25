"""
Portal público de postulación (sin sesión).
"""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import Aplicacion, Candidato, HojaDeVida, HistorialProceso, Rol, Usuario, Vacante
from services.scoring import calcular_score_aplicacion

publico_bp = Blueprint("publico", __name__, url_prefix="/p")


@publico_bp.route("/vacante/<int:vid>")
def vacante_publica(vid: int):
    vac = db.session.get(Vacante, vid)
    if not vac or vac.estado != "abierta":
        return render_template("publico/no_disponible.html"), 404
    return render_template("publico/vacante.html", vacante=vac)


@publico_bp.route("/vacante/<int:vid>/postular", methods=["POST"])
def postular(vid: int):
    vac = db.session.get(Vacante, vid)
    if not vac or vac.estado != "abierta":
        flash("Vacante no disponible.", "danger")
        return redirect(url_for("publico.vacante_publica", vid=vid))

    cedula = request.form.get("cedula", "").strip()
    nombres = request.form.get("nombres", "").strip()
    apellidos = request.form.get("apellidos", "").strip()
    correo = request.form.get("correo", "").strip().lower()
    telefono = request.form.get("telefono", "").strip()

    if not all([cedula, nombres, apellidos, correo]):
        flash("Completa cédula, nombres, apellidos y correo.", "danger")
        return redirect(url_for("publico.vacante_publica", vid=vid))

    cand = db.session.get(Candidato, cedula)
    if not cand:
        cand = Candidato(
            cedula=cedula,
            nombres=nombres,
            apellidos=apellidos,
            correo=correo,
            telefono=telefono or None,
            fuente_captacion="portal_publico",
        )
        db.session.add(cand)
        db.session.flush()
        db.session.add(HojaDeVida(cedula_candidato=cedula, habilidades=[]))
    else:
        cand.nombres = nombres
        cand.apellidos = apellidos
        cand.correo = correo or cand.correo
        cand.telefono = telefono or cand.telefono

    existente = Aplicacion.query.filter_by(cedula_candidato=cedula, id_vacante=vid).first()
    if existente:
        flash("Ya registramos tu postulación a esta vacante.", "info")
        return redirect(url_for("publico.vacante_publica", vid=vid))

    ap = Aplicacion(
        cedula_candidato=cedula,
        id_vacante=vid,
        estado="hoja_de_vida_recibida",
    )
    db.session.add(ap)
    db.session.flush()

    reclutador = _primer_usuario_reclutador()
    if reclutador:
        db.session.add(
            HistorialProceso(
                cedula_candidato=cedula,
                id_aplicacion=ap.id,
                id_usuario=reclutador.id,
                accion="Postulación vía portal público",
                estado_nuevo="hoja_de_vida_recibida",
            )
        )
    try:
        sc = calcular_score_aplicacion(ap)
        if sc is not None:
            ap.score = sc
    except Exception:
        pass

    db.session.commit()
    flash("¡Postulación recibida! Nos pondremos en contacto contigo.", "success")
    return redirect(url_for("publico.vacante_publica", vid=vid))


def _primer_usuario_reclutador() -> Usuario | None:
    rol = Rol.query.filter_by(nombre="reclutador").first()
    if not rol:
        return None
    return Usuario.query.filter_by(id_rol=rol.id, activo=True).first()
