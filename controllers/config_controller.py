"""
Configuración visual y personalización.
"""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import ConfiguracionTema

config_bp = Blueprint("configuracion", __name__, url_prefix="/config")


@config_bp.route("/tema", methods=["GET", "POST"])
@login_required
def tema():
    if not current_user.es_admin:
        flash("Solo administración puede editar el tema.", "danger")
        return redirect(url_for("dashboard.index"))

    cfg = db.session.get(ConfiguracionTema, 1)
    if not cfg:
        cfg = ConfiguracionTema(id=1)
        db.session.add(cfg)
        db.session.flush()

    if request.method == "POST":
        cfg.nombre = (request.form.get("nombre") or cfg.nombre).strip()
        cfg.logo_texto = (request.form.get("logo_texto") or cfg.logo_texto).strip()
        cfg.color_primario = (request.form.get("color_primario") or cfg.color_primario).strip()
        cfg.color_secundario = (request.form.get("color_secundario") or cfg.color_secundario).strip()
        cfg.fondo = (request.form.get("fondo") or cfg.fondo).strip()
        cfg.superficie = (request.form.get("superficie") or cfg.superficie).strip()
        cfg.radio_px = request.form.get("radio_px", type=int) or cfg.radio_px
        cfg.actualizado_por = current_user.id
        db.session.commit()
        flash("Tema actualizado.", "success")
        return redirect(url_for("configuracion.tema"))

    return render_template("config/tema.html", cfg=cfg)
