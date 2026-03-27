"""
TalentFlow — Modelos de base de datos (SQLAlchemy)
Todos los modelos del sistema en un único archivo.
"""

from datetime import date, datetime
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
    empleados_jefe = db.relationship(
        "AsignacionLaboral",
        back_populates="jefe",
        foreign_keys="AsignacionLaboral.id_jefe",
    )
    evaluaciones_desempeno_como_jefe = db.relationship(
        "EvaluacionDesempeno",
        back_populates="jefe_evaluador",
        foreign_keys="EvaluacionDesempeno.id_jefe_evaluador",
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

    @property
    def es_jefe_area(self):
        return self.rol.nombre in ("administrador", "jefe_area")

    @property
    def es_rrhh(self):
        return self.rol.nombre in ("administrador", "rrhh", "reclutador")

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

ESTADOS_LABORALES = [
    ("candidato", "Candidato"),
    ("pre_ingreso", "Pre-ingreso"),
    ("activo", "Activo"),
    ("suspendido", "Suspendido"),
    ("retiro", "Retiro"),
    ("despedido", "Despedido"),
]

ESTADOS_LABORALES_DICT = dict(ESTADOS_LABORALES)

TIPOS_MOVIMIENTO_LABORAL = [
    ("ingreso", "Ingreso"),
    ("ascenso", "Ascenso"),
    ("traslado", "Traslado"),
    ("cambio_sede", "Cambio de sede"),
    ("cambio_cargo", "Cambio de cargo"),
    ("cambio_jefe", "Cambio de jefe"),
    ("ajuste_salarial", "Ajuste salarial"),
]


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


# ══════════════════════════════════════════════════════════════
# CICLO LABORAL (HR)
# ══════════════════════════════════════════════════════════════

class Sede(db.Model):
    __tablename__ = "sedes"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(30), unique=True, nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    ciudad = db.Column(db.String(80))
    direccion = db.Column(db.String(255))
    activa = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    asignaciones = db.relationship("AsignacionLaboral", back_populates="sede")

    def __repr__(self):
        return f"<Sede {self.codigo} - {self.nombre}>"


class Cargo(db.Model):
    __tablename__ = "cargos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(40), unique=True, nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    area = db.Column(db.String(100))
    nivel = db.Column(db.String(50))
    competencias_json = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    asignaciones = db.relationship("AsignacionLaboral", back_populates="cargo")
    evaluaciones_plantillas = db.relationship(
        "PlantillaDesempenoCargo", back_populates="cargo"
    )

    def __repr__(self):
        return f"<Cargo {self.codigo} - {self.nombre}>"


class Empleado(db.Model):
    __tablename__ = "empleados"

    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(20), db.ForeignKey("candidatos.cedula"), unique=True, nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    id_aplicacion_origen = db.Column(db.Integer, db.ForeignKey("aplicaciones.id"))
    estado_laboral = db.Column(db.String(30), default="activo", nullable=False)
    fecha_ingreso = db.Column(db.Date, default=date.today)
    fecha_salida = db.Column(db.Date)
    motivo_salida = db.Column(db.String(120))
    notas = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidato = db.relationship("Candidato")
    usuario = db.relationship("Usuario")
    aplicacion_origen = db.relationship("Aplicacion")
    asignaciones = db.relationship("AsignacionLaboral", back_populates="empleado")
    movimientos = db.relationship("MovimientoLaboral", back_populates="empleado")
    evaluaciones_desempeno = db.relationship("EvaluacionDesempeno", back_populates="empleado")
    novedades_disciplinarias = db.relationship("NovedadDisciplinaria", back_populates="empleado")
    desvinculaciones = db.relationship("Desvinculacion", back_populates="empleado")
    eventos = db.relationship("EventoLaboral", back_populates="empleado")

    @property
    def estado_laboral_legible(self):
        return ESTADOS_LABORALES_DICT.get(self.estado_laboral, self.estado_laboral)

    def __repr__(self):
        return f"<Empleado {self.cedula} estado={self.estado_laboral}>"


class AsignacionLaboral(db.Model):
    __tablename__ = "asignaciones_laborales"

    id = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    id_cargo = db.Column(db.Integer, db.ForeignKey("cargos.id"), nullable=False)
    id_sede = db.Column(db.Integer, db.ForeignKey("sedes.id"), nullable=False)
    id_jefe = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    fecha_inicio = db.Column(db.Date, nullable=False, default=date.today)
    fecha_fin = db.Column(db.Date)
    salario = db.Column(db.Numeric(12, 2))
    es_actual = db.Column(db.Boolean, default=True, nullable=False)
    observaciones = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    empleado = db.relationship("Empleado", back_populates="asignaciones")
    cargo = db.relationship("Cargo", back_populates="asignaciones")
    sede = db.relationship("Sede", back_populates="asignaciones")
    jefe = db.relationship("Usuario", back_populates="empleados_jefe", foreign_keys=[id_jefe])


class MovimientoLaboral(db.Model):
    __tablename__ = "movimientos_laborales"

    id = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    tipo = db.Column(db.String(40), nullable=False)
    id_asignacion_anterior = db.Column(db.Integer, db.ForeignKey("asignaciones_laborales.id"))
    id_asignacion_nueva = db.Column(db.Integer, db.ForeignKey("asignaciones_laborales.id"))
    fecha_movimiento = db.Column(db.Date, default=date.today, nullable=False)
    motivo = db.Column(db.Text)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    empleado = db.relationship("Empleado", back_populates="movimientos")
    usuario = db.relationship("Usuario")
    asignacion_anterior = db.relationship("AsignacionLaboral", foreign_keys=[id_asignacion_anterior])
    asignacion_nueva = db.relationship("AsignacionLaboral", foreign_keys=[id_asignacion_nueva])


class PlantillaDesempenoCargo(db.Model):
    __tablename__ = "plantillas_desempeno_cargo"

    id = db.Column(db.Integer, primary_key=True)
    id_cargo = db.Column(db.Integer, db.ForeignKey("cargos.id"), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)
    criterios_json = db.Column(db.Text, nullable=False)
    activa = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    cargo = db.relationship("Cargo", back_populates="evaluaciones_plantillas")
    evaluaciones = db.relationship("EvaluacionDesempeno", back_populates="plantilla")


class EvaluacionDesempeno(db.Model):
    __tablename__ = "evaluaciones_desempeno"

    id = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    id_plantilla = db.Column(db.Integer, db.ForeignKey("plantillas_desempeno_cargo.id"), nullable=False)
    periodo = db.Column(db.String(40), nullable=False)
    id_jefe_evaluador = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    puntaje_total = db.Column(db.Numeric(6, 2))
    detalle_json = db.Column(db.Text, nullable=False)
    comentario_jefe = db.Column(db.Text)
    estado_aceptacion = db.Column(db.String(30), default="pendiente_empleado")
    comentario_empleado = db.Column(db.Text)
    fecha_evaluacion = db.Column(db.Date, default=date.today)
    fecha_aceptacion = db.Column(db.DateTime)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    empleado = db.relationship("Empleado", back_populates="evaluaciones_desempeno")
    plantilla = db.relationship("PlantillaDesempenoCargo", back_populates="evaluaciones")
    jefe_evaluador = db.relationship(
        "Usuario",
        back_populates="evaluaciones_desempeno_como_jefe",
        foreign_keys=[id_jefe_evaluador],
    )


class NovedadDisciplinaria(db.Model):
    __tablename__ = "novedades_disciplinarias"

    id = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    severidad = db.Column(db.String(30))
    descripcion = db.Column(db.Text, nullable=False)
    estado = db.Column(db.String(30), default="registrada")
    fecha_falta = db.Column(db.Date, default=date.today)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    id_reporta = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    id_aprueba = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    sancion = db.Column(db.Text)

    empleado = db.relationship("Empleado", back_populates="novedades_disciplinarias")
    reporta = db.relationship("Usuario", foreign_keys=[id_reporta])
    aprueba = db.relationship("Usuario", foreign_keys=[id_aprueba])


class Desvinculacion(db.Model):
    __tablename__ = "desvinculaciones"

    id = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    tipo = db.Column(db.String(40), nullable=False)  # retiro_voluntario, despido, fin_contrato
    causa = db.Column(db.Text)
    fecha_efectiva = db.Column(db.Date, nullable=False)
    documento_ref = db.Column(db.String(255))
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    empleado = db.relationship("Empleado", back_populates="desvinculaciones")
    usuario = db.relationship("Usuario")


class EventoLaboral(db.Model):
    __tablename__ = "eventos_laborales"

    id = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(db.Integer, db.ForeignKey("empleados.id"), nullable=False)
    tipo_evento = db.Column(db.String(60), nullable=False)
    descripcion = db.Column(db.String(200), nullable=False)
    metadata_json = db.Column(db.Text)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    fecha_evento = db.Column(db.DateTime, default=datetime.utcnow)

    empleado = db.relationship("Empleado", back_populates="eventos")
    usuario = db.relationship("Usuario")


class ConfiguracionTema(db.Model):
    __tablename__ = "configuracion_tema"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, default="Tema corporativo")
    logo_texto = db.Column(db.String(100), default="TalentFlow")
    color_primario = db.Column(db.String(12), default="#2563eb")
    color_secundario = db.Column(db.String(12), default="#0f172a")
    fondo = db.Column(db.String(12), default="#f5f4f0")
    superficie = db.Column(db.String(12), default="#ffffff")
    radio_px = db.Column(db.Integer, default=10)
    actualizado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)