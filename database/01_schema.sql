-- Ejecutar conectado a la base talentflow_db.
-- Esquema principal de TalentFlow (idempotente).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT
);

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    correo VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    id_rol INTEGER NOT NULL REFERENCES roles(id),
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS candidatos (
    cedula VARCHAR(20) PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    correo VARCHAR(150),
    direccion TEXT,
    ciudad VARCHAR(80),
    fecha_nacimiento DATE,
    fuente_captacion VARCHAR(80),
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS hojas_de_vida (
    id SERIAL PRIMARY KEY,
    cedula_candidato VARCHAR(20) NOT NULL UNIQUE REFERENCES candidatos(cedula),
    experiencia_laboral JSONB,
    formacion_academica JSONB,
    habilidades TEXT[],
    idiomas TEXT[],
    resumen_profesional TEXT,
    fecha_actualizacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vacantes (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT,
    area VARCHAR(100),
    ciudad VARCHAR(80),
    tipo_contrato VARCHAR(50),
    salario_min NUMERIC(12, 2),
    salario_max NUMERIC(12, 2),
    requisitos TEXT,
    estado VARCHAR(30) DEFAULT 'abierta',
    id_responsable INTEGER REFERENCES usuarios(id),
    fecha_apertura DATE DEFAULT CURRENT_DATE,
    fecha_cierre DATE,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS aplicaciones (
    id SERIAL PRIMARY KEY,
    cedula_candidato VARCHAR(20) NOT NULL REFERENCES candidatos(cedula),
    id_vacante INTEGER NOT NULL REFERENCES vacantes(id),
    estado VARCHAR(60) DEFAULT 'hoja_de_vida_recibida',
    fecha_aplicacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_candidato_vacante UNIQUE (cedula_candidato, id_vacante)
);

CREATE TABLE IF NOT EXISTS contactos (
    id SERIAL PRIMARY KEY,
    cedula_candidato VARCHAR(20) REFERENCES candidatos(cedula),
    id_aplicacion INTEGER REFERENCES aplicaciones(id),
    id_usuario INTEGER REFERENCES usuarios(id),
    fecha_contacto TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    canal VARCHAR(50),
    resultado VARCHAR(50),
    observaciones TEXT,
    fecha_registro TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS entrevistas (
    id SERIAL PRIMARY KEY,
    id_aplicacion INTEGER NOT NULL REFERENCES aplicaciones(id),
    tipo VARCHAR(50),
    fecha_programada TIMESTAMP WITHOUT TIME ZONE,
    lugar VARCHAR(150),
    id_entrevistador INTEGER REFERENCES usuarios(id),
    resultado VARCHAR(50) DEFAULT 'pendiente',
    observaciones TEXT,
    fecha_realizada TIMESTAMP WITHOUT TIME ZONE,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evaluaciones_psicologicas (
    id SERIAL PRIMARY KEY,
    id_aplicacion INTEGER NOT NULL REFERENCES aplicaciones(id),
    id_psicologo INTEGER REFERENCES usuarios(id),
    tipo_evaluacion VARCHAR(100),
    fecha_evaluacion DATE,
    resultado VARCHAR(50),
    observaciones TEXT,
    recomendaciones TEXT,
    fecha_registro TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evaluaciones_tecnicas (
    id SERIAL PRIMARY KEY,
    id_aplicacion INTEGER NOT NULL REFERENCES aplicaciones(id),
    tipo VARCHAR(80),
    nombre_prueba VARCHAR(150),
    fecha_aplicacion DATE,
    puntaje NUMERIC(5, 2),
    puntaje_maximo NUMERIC(5, 2),
    resultado VARCHAR(50),
    observaciones TEXT,
    id_evaluador INTEGER REFERENCES usuarios(id),
    fecha_registro TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documentos_adjuntos (
    id SERIAL PRIMARY KEY,
    cedula_candidato VARCHAR(20) REFERENCES candidatos(cedula),
    id_aplicacion INTEGER REFERENCES aplicaciones(id),
    tipo_documento VARCHAR(80),
    nombre_original VARCHAR(255),
    nombre_archivo VARCHAR(255),
    ruta_archivo VARCHAR(500),
    tamano_bytes BIGINT,
    subido_por INTEGER REFERENCES usuarios(id),
    fecha_subida TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS historial_procesos (
    id SERIAL PRIMARY KEY,
    cedula_candidato VARCHAR(20) REFERENCES candidatos(cedula),
    id_aplicacion INTEGER REFERENCES aplicaciones(id),
    id_usuario INTEGER REFERENCES usuarios(id),
    accion VARCHAR(150) NOT NULL,
    estado_anterior VARCHAR(80),
    estado_nuevo VARCHAR(80),
    observaciones TEXT,
    fecha_accion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usuarios_correo ON usuarios(correo);
CREATE INDEX IF NOT EXISTS idx_usuarios_rol ON usuarios(id_rol);
CREATE INDEX IF NOT EXISTS idx_candidatos_activo ON candidatos(activo);
CREATE INDEX IF NOT EXISTS idx_vacantes_estado ON vacantes(estado);
CREATE INDEX IF NOT EXISTS idx_aplicaciones_estado ON aplicaciones(estado);
CREATE INDEX IF NOT EXISTS idx_aplicaciones_vacante ON aplicaciones(id_vacante);
CREATE INDEX IF NOT EXISTS idx_aplicaciones_candidato ON aplicaciones(cedula_candidato);
CREATE INDEX IF NOT EXISTS idx_historial_aplicacion ON historial_procesos(id_aplicacion);
