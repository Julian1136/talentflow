"""
TalentFlow — Servicio de Notificaciones por Email
Centraliza todos los correos automáticos del sistema.

INSTALACIÓN:
  1. pip install Flask-Mail
  2. Agregar variables al .env  (ver sección CONFIG al final)
  3. En app.py, inicializar:
       from services.email_service import mail, init_mail
       init_mail(app)
  4. Guardar este archivo como services/email_service.py
     (crear carpeta: mkdir -p services && touch services/__init__.py)
"""

from flask_mail import Mail, Message
from flask import current_app, render_template_string
from datetime import datetime

mail = Mail()


def init_mail(app):
    """Llamar desde create_app() después de db.init_app(app)."""
    app.config.setdefault("MAIL_SERVER",   "smtp.gmail.com")
    app.config.setdefault("MAIL_PORT",     587)
    app.config.setdefault("MAIL_USE_TLS",  True)
    app.config.setdefault("MAIL_USERNAME", app.config.get("MAIL_USERNAME", ""))
    app.config.setdefault("MAIL_PASSWORD", app.config.get("MAIL_PASSWORD", ""))
    app.config.setdefault("MAIL_DEFAULT_SENDER", (
        "TalentFlow RRHH",
        app.config.get("MAIL_USERNAME", "noreply@talentflow.co"),
    ))
    mail.init_app(app)


# ──────────────────────────────────────────────────────────────────────────────
#  PLANTILLAS HTML de correos (inline — sin archivos externos)
# ──────────────────────────────────────────────────────────────────────────────

_BASE_EMAIL = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: 'Helvetica Neue', Arial, sans-serif; background: #f5f4f0;
           margin: 0; padding: 0; color: #1a1916; }
    .wrap { max-width: 560px; margin: 32px auto; background: #fff;
            border-radius: 12px; overflow: hidden;
            border: 1px solid #e2ddd5; }
    .header { background: #2563eb; padding: 28px 32px; }
    .header h1 { margin: 0; color: #fff; font-size: 20px; font-weight: 600;
                 letter-spacing: -0.3px; }
    .header p { margin: 4px 0 0; color: rgba(255,255,255,.75); font-size: 13px; }
    .body { padding: 28px 32px; }
    .body p { font-size: 15px; line-height: 1.6; margin: 0 0 16px; color: #1a1916; }
    .info-box { background: #f5f4f0; border-radius: 8px; padding: 16px 20px;
                margin: 20px 0; border: 1px solid #e2ddd5; }
    .info-row { display: flex; gap: 12px; padding: 5px 0;
                border-bottom: 1px solid #e2ddd5; font-size: 14px; }
    .info-row:last-child { border-bottom: none; }
    .info-label { color: #6b6760; width: 120px; flex-shrink: 0; font-weight: 500; }
    .info-val { color: #1a1916; flex: 1; }
    .btn { display: inline-block; background: #2563eb; color: #fff !important;
           padding: 12px 24px; border-radius: 8px; text-decoration: none;
           font-size: 14px; font-weight: 500; margin: 8px 0; }
    .footer { padding: 20px 32px; background: #f5f4f0; font-size: 12px;
              color: #9e9b95; border-top: 1px solid #e2ddd5; }
    .badge { display: inline-block; padding: 3px 10px; border-radius: 20px;
             font-size: 12px; font-weight: 600; }
    .badge-blue   { background: #eff6ff; color: #2563eb; }
    .badge-green  { background: #f0fdf4; color: #16a34a; }
    .badge-amber  { background: #fffbeb; color: #d97706; }
    .badge-red    { background: #fef2f2; color: #dc2626; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <h1>🎯 TalentFlow</h1>
      <p>{{ subtitulo }}</p>
    </div>
    <div class="body">
      {{ cuerpo | safe }}
    </div>
    <div class="footer">
      Este mensaje fue generado automáticamente por TalentFlow · Sistema de Gestión de Talento Humano.<br>
      Por favor no respondas a este correo — contacta directamente al equipo de RRHH.
    </div>
  </div>
</body>
</html>
"""


def _render_email(subtitulo: str, cuerpo: str) -> str:
    return render_template_string(_BASE_EMAIL, subtitulo=subtitulo, cuerpo=cuerpo)


def _encolar_reintento(destinatario: str, asunto: str, html: str, error: str) -> None:
    """Persiste un correo fallido para reintento por el scheduler."""
    try:
        from extensions import db
        from models import CorreoColaReintento

        row = CorreoColaReintento(
            destinatario=(destinatario or "")[:255],
            asunto=(asunto or "")[:500],
            cuerpo_html=html or "",
            intentos=0,
            ultimo_error=(error or "")[:2000],
            proximo_intento_en=datetime.utcnow(),
        )
        db.session.add(row)
        db.session.commit()
    except Exception as exc:
        current_app.logger.warning("[EMAIL] No se pudo encolar reintento: %s", exc)
        try:
            from extensions import db

            db.session.rollback()
        except Exception:
            pass


def _enviar(
    destinatario: str,
    asunto: str,
    html: str,
    silencioso: bool = True,
    encolar_reintento_si_falla: bool = True,
) -> bool:
    """Envía el correo. Si silencioso=True, atrapa excepciones sin propagar."""
    try:
        if not destinatario or "@" not in destinatario:
            current_app.logger.warning(f"[EMAIL] Destinatario inválido: {destinatario!r}")
            return False
        if not current_app.config.get("MAIL_USERNAME"):
            current_app.logger.warning("[EMAIL] MAIL_USERNAME no configurado — email omitido.")
            return False

        msg = Message(subject=asunto, recipients=[destinatario], html=html)
        mail.send(msg)
        current_app.logger.info(f"[EMAIL] ✓ Enviado a {destinatario}: {asunto}")
        return True
    except Exception as exc:
        current_app.logger.error(f"[EMAIL] Error al enviar a {destinatario}: {exc}")
        if encolar_reintento_si_falla and silencioso:
            _encolar_reintento(destinatario, asunto, html, str(exc))
        if not silencioso:
            raise
        return False


def reenviar_desde_cola(row) -> bool:
    """Reintenta un registro de CorreoColaReintento (sin volver a encolar al fallar)."""
    return _enviar(
        row.destinatario,
        row.asunto,
        row.cuerpo_html,
        silencioso=True,
        encolar_reintento_si_falla=False,
    )


# ──────────────────────────────────────────────────────────────────────────────
#  FUNCIONES PÚBLICAS — una por tipo de evento
# ──────────────────────────────────────────────────────────────────────────────

def notificar_entrevista_programada(entrevista) -> bool:
    """
    Envía citación al candidato cuando se programa una entrevista.
    Recibe una instancia del modelo Entrevista con sus relaciones cargadas.
    """
    ap        = entrevista.aplicacion
    candidato = ap.candidato
    vacante   = ap.vacante

    if not candidato.correo:
        return False

    tipo_legible = {
        "reclutador":  "Entrevista con Recursos Humanos",
        "jefe_area":   "Entrevista con Jefe de Área",
        "gerencia":    "Entrevista con Gerencia",
    }.get(entrevista.tipo, f"Entrevista — {entrevista.tipo}")

    fecha_fmt  = entrevista.fecha_programada.strftime("%A %d de %B de %Y, %H:%M") \
                 if entrevista.fecha_programada else "Por confirmar"
    lugar_fmt  = entrevista.lugar or "Se informará próximamente"

    cuerpo = f"""
      <p>Hola <strong>{candidato.nombres}</strong>,</p>
      <p>
        Has sido seleccionado(a) para participar en el proceso de selección para la vacante
        <strong>{vacante.titulo}</strong>. Te informamos que tienes una entrevista programada:
      </p>
      <div class="info-box">
        <div class="info-row">
          <span class="info-label">Tipo</span>
          <span class="info-val"><span class="badge badge-blue">{tipo_legible}</span></span>
        </div>
        <div class="info-row">
          <span class="info-label">Fecha y hora</span>
          <span class="info-val">{fecha_fmt}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Lugar / Enlace</span>
          <span class="info-val">{lugar_fmt}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Vacante</span>
          <span class="info-val">{vacante.titulo}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Área</span>
          <span class="info-val">{vacante.area or '—'}</span>
        </div>
      </div>
      <p>
        Por favor confirma tu asistencia respondiendo a <strong>rrhh@empresa.com</strong>
        o comunícate al número de contacto de RRHH.
      </p>
      <p>
        Te recomendamos llegar 10 minutos antes de la hora indicada.
        En caso de algún inconveniente, contáctanos con anticipación.
      </p>
      <p>¡Mucho éxito en tu proceso!</p>
    """

    html = _render_email(
        subtitulo=f"Citación a entrevista · {vacante.titulo}",
        cuerpo=cuerpo,
    )
    return _enviar(
        destinatario=candidato.correo,
        asunto=f"[TalentFlow] Entrevista programada — {vacante.titulo}",
        html=html,
    )


def notificar_entrevista_cancelada(entrevista, motivo: str = "") -> bool:
    """Notifica al candidato que una entrevista fue cancelada."""
    ap = entrevista.aplicacion
    candidato = ap.candidato
    vacante = ap.vacante

    if not candidato.correo:
        return False

    fecha_fmt = (
        entrevista.fecha_programada.strftime("%A %d de %B de %Y, %H:%M")
        if entrevista.fecha_programada
        else "Por confirmar"
    )
    motivo_txt = (motivo or "").strip()
    motivo_html = f"<p><strong>Motivo:</strong> {motivo_txt}</p>" if motivo_txt else ""

    cuerpo = f"""
      <p>Hola <strong>{candidato.nombres}</strong>,</p>
      <p>
        Te informamos que la entrevista programada para la vacante
        <strong>{vacante.titulo}</strong> ({fecha_fmt}) fue cancelada.
      </p>
      {motivo_html}
      <p>
        Nuestro equipo de RRHH te contactará para reprogramar en caso de continuar
        con la siguiente etapa del proceso.
      </p>
    """
    html = _render_email(
        subtitulo=f"Entrevista cancelada · {vacante.titulo}",
        cuerpo=cuerpo,
    )
    return _enviar(
        destinatario=candidato.correo,
        asunto=f"[TalentFlow] Entrevista cancelada — {vacante.titulo}",
        html=html,
    )


def notificar_cambio_estado(aplicacion, estado_anterior: str, estado_nuevo: str) -> bool:
    """
    Notifica al candidato cuando su proceso avanza a un estado relevante.
    Solo envía para estados que el candidato debe saber (no internos).
    """
    ESTADOS_NOTIFICABLES = {
        "contactado":                "Hemos revisado tu hoja de vida",
        "entrevista_programada":     "Tienes una entrevista programada",
        "aprobado":                  "¡Felicitaciones, has sido aprobado!",
        "rechazado":                 "Actualización sobre tu proceso",
        "contratado":                "¡Bienvenido al equipo!",
    }

    if estado_nuevo not in ESTADOS_NOTIFICABLES:
        return False

    candidato = aplicacion.candidato
    vacante   = aplicacion.vacante
    if not candidato.correo:
        return False

    asunto_estado = ESTADOS_NOTIFICABLES[estado_nuevo]

    mensajes_cuerpo = {
        "contactado": f"""
          <p>Hola <strong>{candidato.nombres}</strong>,</p>
          <p>
            Hemos revisado tu hoja de vida para la vacante <strong>{vacante.titulo}</strong>
            y te informamos que tu perfil ha pasado a la siguiente etapa del proceso de selección.
          </p>
          <p>Nuestro equipo de RRHH se pondrá en contacto contigo pronto.</p>
        """,
        "entrevista_programada": f"""
          <p>Hola <strong>{candidato.nombres}</strong>,</p>
          <p>
            Tu proceso para la vacante <strong>{vacante.titulo}</strong> avanza.
            Recibirás próximamente los detalles de tu entrevista.
          </p>
        """,
        "aprobado": f"""
          <p>Hola <strong>{candidato.nombres}</strong>,</p>
          <p>
            Nos complace informarte que has sido <strong>aprobado(a)</strong> en el proceso
            de selección para la vacante <strong>{vacante.titulo}</strong>.
          </p>
          <p>
            El equipo de RRHH se comunicará contigo para los siguientes pasos.
            ¡Felicitaciones por tu excelente desempeño!
          </p>
        """,
        "rechazado": f"""
          <p>Hola <strong>{candidato.nombres}</strong>,</p>
          <p>
            Agradecemos tu participación en el proceso de selección para la vacante
            <strong>{vacante.titulo}</strong>.
          </p>
          <p>
            Después de una cuidadosa evaluación, en esta ocasión hemos avanzado con otros
            candidatos cuyo perfil se ajusta mejor a los requerimientos actuales del cargo.
          </p>
          <p>
            Tu hoja de vida permanecerá en nuestra base de datos para futuras oportunidades.
            Te deseamos mucho éxito en tu búsqueda.
          </p>
        """,
        "contratado": f"""
          <p>Hola <strong>{candidato.nombres}</strong>,</p>
          <p>
            Es un placer informarte que has sido seleccionado(a) para formar parte de nuestro
            equipo en el cargo de <strong>{vacante.titulo}</strong>. ¡Bienvenido(a)!
          </p>
          <p>
            El equipo de RRHH se comunicará contigo para coordinar los detalles de tu
            vinculación, documentación requerida y fecha de inicio.
          </p>
          <p>¡Estamos muy contentos de que te unas a nosotros!</p>
        """,
    }

    cuerpo = mensajes_cuerpo.get(estado_nuevo, "")
    if not cuerpo:
        return False

    html = _render_email(subtitulo=asunto_estado, cuerpo=cuerpo)
    return _enviar(
        destinatario=candidato.correo,
        asunto=f"[TalentFlow] {asunto_estado} — {vacante.titulo}",
        html=html,
    )


def notificar_evaluacion_psicologica(evaluacion) -> bool:
    """Cita al candidato para evaluación psicológica."""
    ap        = evaluacion.aplicacion
    candidato = ap.candidato
    vacante   = ap.vacante
    if not candidato.correo:
        return False

    fecha_fmt = evaluacion.fecha_evaluacion.strftime("%d de %B de %Y") \
                if evaluacion.fecha_evaluacion else "Por confirmar"

    cuerpo = f"""
      <p>Hola <strong>{candidato.nombres}</strong>,</p>
      <p>
        Como parte del proceso de selección para la vacante <strong>{vacante.titulo}</strong>,
        has sido convocado(a) a realizar una evaluación psicológica:
      </p>
      <div class="info-box">
        <div class="info-row">
          <span class="info-label">Tipo de evaluación</span>
          <span class="info-val">{evaluacion.tipo_evaluacion or 'Evaluación psicológica'}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Fecha programada</span>
          <span class="info-val">{fecha_fmt}</span>
        </div>
      </div>
      <p>
        Esta evaluación hace parte del proceso estándar de selección y es completamente
        confidencial. Los resultados son utilizados únicamente para fines de la selección.
      </p>
      <p>Por favor confirma tu asistencia respondiendo este correo o comunicándote con RRHH.</p>
    """

    html = _render_email(
        subtitulo=f"Evaluación psicológica · {vacante.titulo}",
        cuerpo=cuerpo,
    )
    return _enviar(
        destinatario=candidato.correo,
        asunto=f"[TalentFlow] Evaluación psicológica programada — {vacante.titulo}",
        html=html,
    )


def notificar_nuevo_candidato_a_reclutador(aplicacion, reclutador_correo: str) -> bool:
    """Avisa al reclutador responsable cuando llega una nueva aplicación."""
    candidato = aplicacion.candidato
    vacante   = aplicacion.vacante

    cuerpo = f"""
      <p>Hola,</p>
      <p>
        Se ha registrado una nueva aplicación para la vacante
        <strong>{vacante.titulo}</strong>:
      </p>
      <div class="info-box">
        <div class="info-row">
          <span class="info-label">Candidato</span>
          <span class="info-val">{candidato.nombre_completo}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Cédula</span>
          <span class="info-val">{candidato.cedula}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Correo</span>
          <span class="info-val">{candidato.correo or '—'}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Fuente</span>
          <span class="info-val">{candidato.fuente_captacion or '—'}</span>
        </div>
        <div class="info-row">
          <span class="info-label">Fecha</span>
          <span class="info-val">{aplicacion.fecha_aplicacion.strftime('%d/%m/%Y %H:%M')}</span>
        </div>
      </div>
      <p>Ingresa al sistema para revisar el perfil completo y avanzar el proceso.</p>
    """

    html = _render_email(
        subtitulo=f"Nueva aplicación · {vacante.titulo}",
        cuerpo=cuerpo,
    )
    return _enviar(
        destinatario=reclutador_correo,
        asunto=f"[TalentFlow] Nueva aplicación: {candidato.nombre_completo} → {vacante.titulo}",
        html=html,
    )


def notificar_recordatorio_entrevista_24h(entrevista) -> bool:
    """Recordatorio al candidato ~24 h antes (invocado desde el scheduler)."""
    if not getattr(entrevista, "fecha_programada", None):
        return False
    ap = entrevista.aplicacion
    if not ap:
        return False
    candidato = ap.candidato
    vacante = ap.vacante
    if not candidato or not candidato.correo:
        return False
    if getattr(entrevista, "resultado", "") != "pendiente":
        return False

    fecha_fmt = entrevista.fecha_programada.strftime("%A %d de %B de %Y, %H:%M")
    lugar_fmt = entrevista.lugar or "—"
    cuerpo = f"""
      <p>Hola <strong>{candidato.nombres}</strong>,</p>
      <p>Te recordamos que mañana tienes entrevista para <strong>{vacante.titulo}</strong>.</p>
      <div class="info-box">
        <div class="info-row"><span class="info-label">Fecha</span><span class="info-val">{fecha_fmt}</span></div>
        <div class="info-row"><span class="info-label">Lugar</span><span class="info-val">{lugar_fmt}</span></div>
      </div>
      <p>¡Te deseamos mucho éxito!</p>
    """
    html = _render_email(subtitulo="Recordatorio de entrevista", cuerpo=cuerpo)
    return _enviar(
        destinatario=candidato.correo,
        asunto=f"[TalentFlow] Recordatorio: entrevista · {vacante.titulo}",
        html=html,
    )


# ──────────────────────────────────────────────────────────────────────────────
#  CONFIG — Agregar al .env
# ──────────────────────────────────────────────────────────────────────────────
"""
# Email (Gmail con App Password recomendado)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=rrhh@tuempresa.com
MAIL_PASSWORD=xxxx_xxxx_xxxx_xxxx    # App Password de Google, no la contraseña normal

# Para Outlook/Office365:
# MAIL_SERVER=smtp.office365.com
# MAIL_PORT=587
"""