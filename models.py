"""
TalentFlow — Modelos de base de datos (SQLAlchemy)
Todos los modelos del sistema en un único archivo.
"""

from datetime import datetime
from flask_login import UserMixin
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


# ══════════════════════════════════════════════════════════════
# ROLES Y USUARIOS
# ══════════════════════════════════════════════════════════════

class Rol(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text)

    usuarios = db.relationship("Usuario", back_populates="rol")

    def __repr__(self):
        return f"<Rol {self.nombre}>"


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(20), unique=True, nullable=False)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    id_rol = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    rol = db.relationship("Rol", back_populates="usuarios")
    contactos_realizados = db.relationship("Contacto", back_populates="usuario")
    entrevistas_conducidas = db.relationship("Entrevista", back_populates="entrevistador")
    evaluaciones_plantilla_enviadas = db.relationship(
        "EvaluacionPlantillaRespuesta", back_populates="usuario"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        ph = (self.password_hash or "").strip()
        if not ph:
            return False
        # Semilla SQL (pgcrypto crypt + gen_salt('bf')) = bcrypt; Werkzeug usa pbkdf2:sha256:...
        if ph.startswith(("$2a$", "$2b$", "$2y$")):
            try:
                return bcrypt.checkpw(
                    password.encode("utf-8"),
                    ph.encode("utf-8"),
                )
            except (ValueError, TypeError):
                return False
        return check_password_hash(ph, password)

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def es_admin(self):
        return self.rol.nombre == "administrador"

    @property
    def es_reclutador(self):
        return self.rol.nombre in ("administrador", "reclutador")

    @property
    def es_psicologo(self):
        return self.rol.nombre == "psicologo"

    def __repr__(self):
        return f"<Usuario {self.correo}>"


# ══════════════════════════════════════════════════════════════
# CANDIDATOS
# ══════════════════════════════════════════════════════════════

class Candidato(db.Model):
    __tablename__ = "candidatos"

    cedula = db.Column(db.String(20), primary_key=True)
    nombres = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    correo = db.Column(db.String(150))
    direccion = db.Column(db.Text)
    ciudad = db.Column(db.String(80))
    fecha_nacimiento = db.Column(db.Date)
    fuente_captacion = db.Column(db.String(80))  # Elempleo, Computrabajo, etc.
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    hoja_de_vida = db.relationship("HojaDeVida", back_populates="candidato", uselist=False)
    aplicaciones = db.relationship("Aplicacion", back_populates="candidato")
    contactos = db.relationship("Contacto", back_populates="candidato")
    documentos = db.relationship("DocumentoAdjunto", back_populates="candidato")
    historial = db.relationship("HistorialProceso", back_populates="candidato")

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def ultimo_estado(self):
        """Retorna el estado más reciente entre todas sus aplicaciones."""
        if not self.aplicaciones:
            return "Sin aplicaciones"
        return self.aplicaciones[-1].estado_legible

    def __repr__(self):
        return f"<Candidato {self.cedula} - {self.nombre_completo}>"


class HojaDeVida(db.Model):
    __tablename__ = "hojas_de_vida"

    id = db.Column(db.Integer, primary_key=True)
    cedula_candidato = db.Column(
        db.String(20), db.ForeignKey("candidatos.cedula"), nullable=False, unique=True
    )
    experiencia_laboral = db.Column(db.JSON)   # Lista de dicts
    formacion_academica = db.Column(db.JSON)   # Lista de dicts
    habilidades = db.Column(db.ARRAY(db.Text))
    idiomas = db.Column(db.ARRAY(db.Text))
    resumen_profesional = db.Column(db.Text)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidato = db.relationship("Candidato", back_populates="hoja_de_vida")

    def __repr__(self):
        return f"<HojaDeVida de {self.cedula_candidato}>"


# ══════════════════════════════════════════════════════════════
# VACANTES Y APLICACIONES
# ══════════════════════════════════════════════════════════════

ESTADOS_APLICACION = [
    ("hoja_de_vida_recibida", "Hoja de vida recibida"),
    ("en_revision", "En revisión"),
    ("contactado", "Contactado"),
    ("entrevista_programada", "Entrevista programada"),
    ("entrevista_realizada", "Entrevista realizada"),
    ("evaluacion_psicologica_pendiente", "Evaluación psicológica pendiente"),
    ("en_pruebas_tecnicas", "En pruebas técnicas"),
    ("aprobado", "Aprobado"),
    ("rechazado", "Rechazado"),
    ("contratado", "Contratado"),
]

ESTADOS_DICT = dict(ESTADOS_APLICACION)


class Vacante(db.Model):
    __tablename__ = "vacantes"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    area = db.Column(db.String(100))
    ciudad = db.Column(db.String(80))
    tipo_contrato = db.Column(db.String(50))
    salario_min = db.Column(db.Numeric(12, 2))
    salario_max = db.Column(db.Numeric(12, 2))
    requisitos = db.Column(db.Text)
    estado = db.Column(db.String(30), default="abierta")
    id_responsable = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    fecha_apertura = db.Column(db.Date, default=datetime.utcnow)
    fecha_cierre = db.Column(db.Date)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    aplicaciones = db.relationship("Aplicacion", back_populates="vacante")

    @property
    def total_candidatos(self):
        return len(self.aplicaciones)

    def __repr__(self):
        return f"<Vacante {self.titulo}>"


class Aplicacion(db.Model):
    __tablename__ = "aplicaciones"

    id = db.Column(db.Integer, primary_key=True)
    cedula_candidato = db.Column(
        db.String(20), db.ForeignKey("candidatos.cedula"), nullable=False
    )
    id_vacante = db.Column(db.Integer, db.ForeignKey("vacantes.id"), nullable=False)
    estado = db.Column(db.String(60), default="hoja_de_vida_recibida")
    fecha_aplicacion = db.Column(db.DateTime, default=datetime.utcnow)
    score = db.Column(db.Numeric(5, 2))

    candidato = db.relationship("Candidato", back_populates="aplicaciones")
    vacante = db.relationship("Vacante", back_populates="aplicaciones")
    contactos = db.relationship("Contacto", back_populates="aplicacion")
    entrevistas = db.relationship("Entrevista", back_populates="aplicacion")
    evaluaciones_psicologicas = db.relationship("EvaluacionPsicologica", back_populates="aplicacion")
    evaluaciones_tecnicas = db.relationship("EvaluacionTecnica", back_populates="aplicacion")
    evaluaciones_plantilla = db.relationship(
        "EvaluacionPlantillaRespuesta", back_populates="aplicacion"
    )
    historial = db.relationship("HistorialProceso", back_populates="aplicacion")

    @property
    def estado_legible(self):
        return ESTADOS_DICT.get(self.estado, self.estado)

    __table_args__ = (
        db.UniqueConstraint("cedula_candidato", "id_vacante", name="uq_candidato_vacante"),
    )

    def __repr__(self):
        return f"<Aplicacion {self.cedula_candidato} → Vacante {self.id_vacante}>"


# ══════════════════════════════════════════════════════════════
# PROCESO DE SELECCIÓN
# ══════════════════════════════════════════════════════════════

class Contacto(db.Model):
    __tablename__ = "contactos"

    id = db.Column(db.Integer, primary_key=True)
    cedula_candidato = db.Column(db.String(20), db.ForeignKey("candidatos.cedula"))
    id_aplicacion = db.Column(db.Integer, db.ForeignKey("aplicaciones.id"))
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    fecha_contacto = db.Column(db.DateTime, nullable=False)
    canal = db.Column(db.String(50))  # telefono, correo, whatsapp, presencial
    resultado = db.Column(db.String(50))  # exitoso, sin_respuesta, reagendado
    observaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    candidato = db.relationship("Candidato", back_populates="contactos")
    aplicacion = db.relationship("Aplicacion", back_populates="contactos")
    usuario = db.relationship("Usuario", back_populates="contactos_realizados")


class Entrevista(db.Model):
    __tablename__ = "entrevistas"

    id = db.Column(db.Integer, primary_key=True)
    id_aplicacion = db.Column(db.Integer, db.ForeignKey("aplicaciones.id"), nullable=False)
    tipo = db.Column(db.String(50))  # reclutador, jefe_area, gerencia
    fecha_programada = db.Column(db.DateTime)
    lugar = db.Column(db.String(150))
    id_entrevistador = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    resultado = db.Column(db.String(50), default="pendiente")
    observaciones = db.Column(db.Text)
    fecha_realizada = db.Column(db.DateTime)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    aplicacion = db.relationship("Aplicacion", back_populates="entrevistas")
    entrevistador = db.relationship("Usuario", back_populates="entrevistas_conducidas")


class EvaluacionPsicologica(db.Model):
    __tablename__ = "evaluaciones_psicologicas"

    id = db.Column(db.Integer, primary_key=True)
    id_aplicacion = db.Column(db.Integer, db.ForeignKey("aplicaciones.id"), nullable=False)
    id_psicologo = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    tipo_evaluacion = db.Column(db.String(100))
    fecha_evaluacion = db.Column(db.Date)
    resultado = db.Column(db.String(50))  # apto, no_apto, apto_con_observaciones
    observaciones = db.Column(db.Text)
    recomendaciones = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    aplicacion = db.relationship("Aplicacion", back_populates="evaluaciones_psicologicas")


class PlantillaEvaluacion(db.Model):
    """Criterios de evaluación en JSON: lista de {id, texto, peso, max}."""

    __tablename__ = "plantillas_evaluacion"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    criterios_json = db.Column(db.Text, nullable=False)
    activa = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    respuestas = db.relationship(
        "EvaluacionPlantillaRespuesta", back_populates="plantilla"
    )


class EvaluacionPlantillaRespuesta(db.Model):
    __tablename__ = "evaluaciones_plantilla_respuestas"

    id = db.Column(db.Integer, primary_key=True)
    id_aplicacion = db.Column(db.Integer, db.ForeignKey("aplicaciones.id"), nullable=False)
    id_plantilla = db.Column(db.Integer, db.ForeignKey("plantillas_evaluacion.id"), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    respuestas_json = db.Column(db.Text, nullable=False)
    puntaje_total = db.Column(db.Numeric(6, 2))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    aplicacion = db.relationship("Aplicacion", back_populates="evaluaciones_plantilla")
    plantilla = db.relationship("PlantillaEvaluacion", back_populates="respuestas")
    usuario = db.relationship("Usuario", back_populates="evaluaciones_plantilla_enviadas")


class EvaluacionTecnica(db.Model):
    __tablename__ = "evaluaciones_tecnicas"

    id = db.Column(db.Integer, primary_key=True)
    id_aplicacion = db.Column(db.Integer, db.ForeignKey("aplicaciones.id"), nullable=False)
    tipo = db.Column(db.String(80))  # tecnica, psicotecnica, conocimiento
    nombre_prueba = db.Column(db.String(150))
    fecha_aplicacion = db.Column(db.Date)
    puntaje = db.Column(db.Numeric(5, 2))
    puntaje_maximo = db.Column(db.Numeric(5, 2))
    resultado = db.Column(db.String(50))  # aprobado, reprobado, pendiente
    observaciones = db.Column(db.Text)
    id_evaluador = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    aplicacion = db.relationship("Aplicacion", back_populates="evaluaciones_tecnicas")


class FirmaAceptacion(db.Model):
    __tablename__ = "firma_aceptaciones"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(96), unique=True, nullable=False)
    id_aplicacion = db.Column(db.Integer, db.ForeignKey("aplicaciones.id"))
    cedula_candidato = db.Column(db.String(20), db.ForeignKey("candidatos.cedula"))
    tipo_documento = db.Column(db.String(100))
    hash_documento = db.Column(db.String(128))
    ip_aceptacion = db.Column(db.String(64))
    user_agent = db.Column(db.Text)
    fecha_aceptacion = db.Column(db.DateTime, default=datetime.utcnow)


class DocumentoAdjunto(db.Model):
    __tablename__ = "documentos_adjuntos"

    id = db.Column(db.Integer, primary_key=True)
    cedula_candidato = db.Column(db.String(20), db.ForeignKey("candidatos.cedula"))
    id_aplicacion = db.Column(db.Integer, db.ForeignKey("aplicaciones.id"))
    tipo_documento = db.Column(db.String(80))
    nombre_original = db.Column(db.String(255))
    nombre_archivo = db.Column(db.String(255))  # UUID en disco
    ruta_archivo = db.Column(db.String(500))
    tamano_bytes = db.Column(db.BigInteger)
    subido_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)

    candidato = db.relationship("Candidato", back_populates="documentos")


class HistorialProceso(db.Model):
    __tablename__ = "historial_procesos"

    id = db.Column(db.Integer, primary_key=True)
    cedula_candidato = db.Column(db.String(20), db.ForeignKey("candidatos.cedula"))
    id_aplicacion = db.Column(db.Integer, db.ForeignKey("aplicaciones.id"))
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    accion = db.Column(db.String(150), nullable=False)
    estado_anterior = db.Column(db.String(80))
    estado_nuevo = db.Column(db.String(80))
    observaciones = db.Column(db.Text)
    fecha_accion = db.Column(db.DateTime, default=datetime.utcnow)

    candidato = db.relationship("Candidato", back_populates="historial")
    aplicacion = db.relationship("Aplicacion", back_populates="historial")