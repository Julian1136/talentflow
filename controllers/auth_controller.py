"""
TalentFlow — Controlador de Autenticación
Maneja login, logout y registro de usuarios del sistema.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError

from models import Usuario, Rol
from extensions import db, limiter

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("25 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        password = request.form.get("password", "")

        usuario = Usuario.query.filter_by(correo=correo, activo=True).first()

        if usuario and usuario.check_password(password):
            login_user(usuario, remember=request.form.get("recordar") == "on")
            flash(f"Bienvenido, {usuario.nombres}.", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))

        flash("Correo o contraseña incorrectos.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/usuarios", methods=["GET", "POST"])
@login_required
def gestionar_usuarios():
    if not current_user.es_admin:
        flash("No tienes permisos para esta sección.", "danger")
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        accion = request.form.get("accion")

        if accion == "crear":
            rol = Rol.query.filter_by(nombre=request.form.get("rol")).first()
            if not rol:
                flash("Rol no válido.", "danger")
                return redirect(url_for("auth.gestionar_usuarios"))

            cedula = (request.form.get("cedula") or "").strip()
            correo = (request.form.get("correo") or "").strip().lower()

            if not cedula or not correo:
                flash("Cédula y correo son obligatorios.", "warning")
                return redirect(url_for("auth.gestionar_usuarios"))

            if Usuario.query.filter_by(cedula=cedula).first():
                flash("Ya existe un usuario con esa cédula.", "warning")
                return redirect(url_for("auth.gestionar_usuarios"))

            if Usuario.query.filter_by(correo=correo).first():
                flash("Ya existe un usuario con ese correo.", "warning")
                return redirect(url_for("auth.gestionar_usuarios"))

            nuevo = Usuario(
                cedula=cedula,
                nombres=(request.form.get("nombres") or "").strip(),
                apellidos=(request.form.get("apellidos") or "").strip(),
                correo=correo,
                id_rol=rol.id,
            )
            nuevo.set_password(request.form.get("password"))
            try:
                db.session.add(nuevo)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash(
                    "No se pudo crear el usuario: la cédula o el correo ya están registrados.",
                    "danger",
                )
                return redirect(url_for("auth.gestionar_usuarios"))
            flash(f"Usuario {nuevo.nombre_completo} creado.", "success")

        elif accion == "desactivar":
            uid = request.form.get("usuario_id")
            u = db.session.get(Usuario, uid)
            if u and u.id != current_user.id:
                u.activo = False
                db.session.commit()
                flash("Usuario desactivado.", "info")

    usuarios = Usuario.query.order_by(Usuario.nombres).all()
    roles = Rol.query.all()
    return render_template("auth/usuarios.html", usuarios=usuarios, roles=roles)
