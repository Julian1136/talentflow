"""
TalentFlow — Controlador Kanban
Vista de pipeline visual con drag & drop y API JSON para actualizaciones en tiempo real.

INSTALACIÓN:
  1. Guardar como controllers/kanban_controller.py
  2. En app.py, importar y registrar:
       from controllers.kanban_controller import kanban_bp
       app.register_blueprint(kanban_bp)
  3. En base.html sidebar, agregar enlace al Kanban (ver instrucción al final del archivo)
"""

from flask import Blueprint, render_template, request, jsonify, abort, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Aplicacion, HistorialProceso, Vacante, ESTADOS_APLICACION, ESTADOS_DICT
from extensions import db
from sqlalchemy import func

kanban_bp = Blueprint("kanban", __name__, url_prefix="/kanban")


# ─── Vista principal ──────────────────────────────────────────────────────────

@kanban_bp.route("/")
@login_required
def index():
    """
    Renderiza el tablero Kanban.
    Permite filtrar por vacante con ?vacante=<id>
    """
    if not current_user.puede_ver_seleccion:
        flash("No tiene permisos para el tablero Kanban.", "danger")
        return redirect(url_for("dashboard.index"))

    vacantes = Vacante.query.filter_by(estado="abierta").order_by(Vacante.titulo).all()
    vacante_id = request.args.get("vacante", type=int)
    vacante_sel = None

    # Construir columnas: {codigo: {nombre, color, aplicaciones[]}}
    columnas = {}
    for codigo, nombre in ESTADOS_APLICACION:
        columnas[codigo] = {
            "nombre": nombre,
            "codigo": codigo,
            "aplicaciones": [],
        }

    query = Aplicacion.query.join(Aplicacion.candidato).join(Aplicacion.vacante)

    if vacante_id:
        query = query.filter(Aplicacion.id_vacante == vacante_id)
        vacante_sel = db.session.get(Vacante, vacante_id)

    aplicaciones = query.order_by(Aplicacion.fecha_aplicacion.desc()).all()

    for ap in aplicaciones:
        if ap.estado in columnas:
            columnas[ap.estado]["aplicaciones"].append(ap)

    # Conteos por columna para las insignias
    totales = {codigo: len(datos["aplicaciones"]) for codigo, datos in columnas.items()}
    total_general = sum(totales.values())

    return render_template(
        "kanban/index.html",
        columnas=columnas,
        estados=ESTADOS_APLICACION,
        vacantes=vacantes,
        vacante_sel=vacante_sel,
        totales=totales,
        total_general=total_general,
    )


# ─── API: mover tarjeta (drag & drop) ────────────────────────────────────────

@kanban_bp.route("/mover", methods=["POST"])
@login_required
def mover_tarjeta():
    """
    Endpoint AJAX llamado por SortableJS al soltar una tarjeta.
    Body JSON: { app_id: int, nuevo_estado: str, posicion: int }
    Respuesta: { ok: bool, estado_legible: str, error?: str }
    """
    if not current_user.es_reclutador:
        return jsonify({"ok": False, "error": "Sin permisos para mover candidatos."}), 403

    data = request.get_json(silent=True) or {}
    app_id = data.get("app_id")
    nuevo_estado = data.get("nuevo_estado", "").strip()

    if not app_id or not nuevo_estado:
        return jsonify({"ok": False, "error": "Datos incompletos."}), 400

    estados_validos = [e[0] for e in ESTADOS_APLICACION]
    if nuevo_estado not in estados_validos:
        return jsonify({"ok": False, "error": "Estado no válido."}), 400

    aplicacion = db.session.get(Aplicacion, app_id)
    if not aplicacion:
        return jsonify({"ok": False, "error": "Aplicación no encontrada."}), 404

    estado_anterior = aplicacion.estado
    if estado_anterior == nuevo_estado:
        # Sin cambio real; igualmente responder OK para no bloquear el UI
        return jsonify({
            "ok": True,
            "estado_legible": aplicacion.estado_legible,
            "sin_cambio": True,
        })

    aplicacion.estado = nuevo_estado

    historial = HistorialProceso(
        cedula_candidato=aplicacion.cedula_candidato,
        id_aplicacion=aplicacion.id,
        id_usuario=current_user.id,
        accion=f"Movido en Kanban: {estado_anterior} → {nuevo_estado}",
        estado_anterior=estado_anterior,
        estado_nuevo=nuevo_estado,
    )
    db.session.add(historial)
    db.session.commit()

    return jsonify({
        "ok": True,
        "estado_legible": aplicacion.estado_legible,
        "estado_codigo": nuevo_estado,
        "candidato": aplicacion.candidato.nombre_completo,
    })


# ─── API: datos de columna (para refrescar sin recargar página) ───────────────

@kanban_bp.route("/columna/<estado>")
@login_required
def datos_columna(estado):
    """
    Retorna JSON con las aplicaciones de una columna específica.
    Útil para refrescar una columna tras cambios externos.
    """
    if not current_user.puede_ver_seleccion:
        abort(403)

    estados_validos = [e[0] for e in ESTADOS_APLICACION]
    if estado not in estados_validos:
        abort(400)

    vacante_id = request.args.get("vacante", type=int)
    query = Aplicacion.query.filter_by(estado=estado)
    if vacante_id:
        query = query.filter_by(id_vacante=vacante_id)

    aplicaciones = query.order_by(Aplicacion.fecha_aplicacion.desc()).all()

    return jsonify({
        "estado": estado,
        "nombre": ESTADOS_DICT.get(estado, estado),
        "total": len(aplicaciones),
        "aplicaciones": [
            {
                "id": ap.id,
                "candidato": ap.candidato.nombre_completo,
                "cedula": ap.cedula_candidato,
                "vacante": ap.vacante.titulo,
                "fecha": ap.fecha_aplicacion.strftime("%d/%m/%Y"),
                "skills": (ap.candidato.hoja_de_vida.habilidades[:3]
                           if ap.candidato.hoja_de_vida and ap.candidato.hoja_de_vida.habilidades
                           else []),
                "fuente": ap.candidato.fuente_captacion or "",
            }
            for ap in aplicaciones
        ],
    })


# ─── API: resumen estadístico para el header del Kanban ───────────────────────

@kanban_bp.route("/stats")
@login_required
def stats():
    """Devuelve conteos rápidos para actualizar badges sin recargar."""
    if not current_user.puede_ver_seleccion:
        abort(403)

    vacante_id = request.args.get("vacante", type=int)

    base = db.session.query(Aplicacion.estado, func.count(Aplicacion.id))
    if vacante_id:
        base = base.filter(Aplicacion.id_vacante == vacante_id)

    rows = base.group_by(Aplicacion.estado).all()
    conteos = {estado: count for estado, count in rows}

    return jsonify({
        "ok": True,
        "conteos": conteos,
        "total": sum(conteos.values()),
    })


# ─────────────────────────────────────────────────────────────────────────────
# INSTRUCCIÓN: agregar en base.html, dentro del bloque <nav class="sidebar-nav">
# bajo la sección "Selección", DESPUÉS del enlace de Candidatos:
#
#   <a href="{{ url_for('kanban.index') }}"
#      class="nav-link {% if request.blueprint == 'kanban' %}active{% endif %}">
#     <span class="icon">🗂</span> Kanban
#   </a>
# ─────────────────────────────────────────────────────────────────────────────