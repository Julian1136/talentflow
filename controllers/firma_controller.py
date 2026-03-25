"""
Firma electrónica simulada: token único y registro de aceptación.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from extensions import db
from models import Aplicacion, FirmaAceptacion

firma_bp = Blueprint("firma", __name__, url_prefix="/firma")


@firma_bp.route("/aceptar/<token>", methods=["GET", "POST"])
def aceptar(token: str):
    reg = FirmaAceptacion.query.filter_by(token=token).first()
    if not reg:
        return render_template("firma/error.html", mensaje="Enlace inválido o expirado."), 404

    if request.method == "POST":
        reg.ip_aceptacion = (request.headers.get("X-Forwarded-For") or request.remote_addr or "")[
            :64
        ]
        reg.user_agent = (request.headers.get("User-Agent") or "")[:2000]
        reg.fecha_aceptacion = datetime.utcnow()
        db.session.commit()
        return render_template("firma/gracias.html", reg=reg)

    return render_template("firma/aceptar.html", reg=reg)


@firma_bp.route("/preparar/<int:app_id>", methods=["POST"])
@login_required
def preparar(app_id: int):
    if not current_user.es_reclutador:
        flash("Sin permisos.", "danger")
        return redirect(url_for("proceso.detalle", app_id=app_id))

    aplicacion = db.session.get(Aplicacion, app_id)
    if not aplicacion:
        flash("Aplicación no encontrada.", "danger")
        return redirect(url_for("dashboard.index"))

    tipo = (request.form.get("tipo_documento") or "contrato").strip()[:100]
    raw = f"{app_id}:{aplicacion.cedula_candidato}:{tipo}:{secrets.token_hex(8)}"
    doc_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    token = secrets.token_urlsafe(32)

    reg = FirmaAceptacion(
        token=token,
        id_aplicacion=app_id,
        cedula_candidato=aplicacion.cedula_candidato,
        tipo_documento=tipo,
        hash_documento=doc_hash,
    )
    db.session.add(reg)
    db.session.commit()

    url = url_for("firma.aceptar", token=token, _external=True)
    flash(f"Enlace de aceptación generado. Copia y envía al candidato: {url}", "success")
    return redirect(url_for("proceso.detalle", app_id=app_id))
