-- Fase HR end-to-end: ciclo laboral, desempeño, disciplina y offboarding.
-- Ejecutar después de 05_firma_aceptaciones.sql

CREATE TABLE IF NOT EXISTS sedes (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(30) UNIQUE NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    ciudad VARCHAR(80),
    direccion VARCHAR(255),
    activa BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cargos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(40) UNIQUE NOT NULL,
    nombre VARCHAR(120) NOT NULL,
    area VARCHAR(100),
    nivel VARCHAR(50),
    competencias_json TEXT,
    activo BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS empleados (
    id SERIAL PRIMARY KEY,
    cedula VARCHAR(20) UNIQUE NOT NULL REFERENCES candidatos(cedula),
    id_usuario INTEGER REFERENCES usuarios(id),
    id_aplicacion_origen INTEGER REFERENCES aplicaciones(id),
    estado_laboral VARCHAR(30) NOT NULL DEFAULT 'activo',
    fecha_ingreso DATE DEFAULT CURRENT_DATE,
    fecha_salida DATE,
    motivo_salida VARCHAR(120),
    notas TEXT,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS asignaciones_laborales (
    id SERIAL PRIMARY KEY,
    id_empleado INTEGER NOT NULL REFERENCES empleados(id),
    id_cargo INTEGER NOT NULL REFERENCES cargos(id),
    id_sede INTEGER NOT NULL REFERENCES sedes(id),
    id_jefe INTEGER REFERENCES usuarios(id),
    fecha_inicio DATE NOT NULL DEFAULT CURRENT_DATE,
    fecha_fin DATE,
    salario NUMERIC(12,2),
    es_actual BOOLEAN NOT NULL DEFAULT TRUE,
    observaciones TEXT,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS movimientos_laborales (
    id SERIAL PRIMARY KEY,
    id_empleado INTEGER NOT NULL REFERENCES empleados(id),
    tipo VARCHAR(40) NOT NULL,
    id_asignacion_anterior INTEGER REFERENCES asignaciones_laborales(id),
    id_asignacion_nueva INTEGER REFERENCES asignaciones_laborales(id),
    fecha_movimiento DATE NOT NULL DEFAULT CURRENT_DATE,
    motivo TEXT,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id),
    fecha_registro TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS plantillas_desempeno_cargo (
    id SERIAL PRIMARY KEY,
    id_cargo INTEGER NOT NULL REFERENCES cargos(id),
    nombre VARCHAR(200) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    criterios_json TEXT NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_plantilla_desempeno_version UNIQUE(id_cargo, nombre, version)
);

CREATE TABLE IF NOT EXISTS evaluaciones_desempeno (
    id SERIAL PRIMARY KEY,
    id_empleado INTEGER NOT NULL REFERENCES empleados(id),
    id_plantilla INTEGER NOT NULL REFERENCES plantillas_desempeno_cargo(id),
    periodo VARCHAR(40) NOT NULL,
    id_jefe_evaluador INTEGER NOT NULL REFERENCES usuarios(id),
    puntaje_total NUMERIC(6,2),
    detalle_json TEXT NOT NULL,
    comentario_jefe TEXT,
    estado_aceptacion VARCHAR(30) DEFAULT 'pendiente_empleado',
    comentario_empleado TEXT,
    fecha_evaluacion DATE DEFAULT CURRENT_DATE,
    fecha_aceptacion TIMESTAMP WITHOUT TIME ZONE,
    fecha_registro TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS novedades_disciplinarias (
    id SERIAL PRIMARY KEY,
    id_empleado INTEGER NOT NULL REFERENCES empleados(id),
    tipo VARCHAR(50) NOT NULL,
    severidad VARCHAR(30),
    descripcion TEXT NOT NULL,
    estado VARCHAR(30) DEFAULT 'registrada',
    fecha_falta DATE DEFAULT CURRENT_DATE,
    fecha_registro TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    id_reporta INTEGER NOT NULL REFERENCES usuarios(id),
    id_aprueba INTEGER REFERENCES usuarios(id),
    sancion TEXT
);

CREATE TABLE IF NOT EXISTS desvinculaciones (
    id SERIAL PRIMARY KEY,
    id_empleado INTEGER NOT NULL REFERENCES empleados(id),
    tipo VARCHAR(40) NOT NULL,
    causa TEXT,
    fecha_efectiva DATE NOT NULL,
    documento_ref VARCHAR(255),
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id),
    fecha_registro TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS eventos_laborales (
    id SERIAL PRIMARY KEY,
    id_empleado INTEGER NOT NULL REFERENCES empleados(id),
    tipo_evento VARCHAR(60) NOT NULL,
    descripcion VARCHAR(200) NOT NULL,
    metadata_json TEXT,
    id_usuario INTEGER REFERENCES usuarios(id),
    fecha_evento TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS configuracion_tema (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL DEFAULT 'Tema corporativo',
    logo_texto VARCHAR(100) DEFAULT 'TalentFlow',
    color_primario VARCHAR(12) DEFAULT '#2563eb',
    color_secundario VARCHAR(12) DEFAULT '#0f172a',
    fondo VARCHAR(12) DEFAULT '#f5f4f0',
    superficie VARCHAR(12) DEFAULT '#ffffff',
    radio_px INTEGER DEFAULT 10,
    actualizado_por INTEGER REFERENCES usuarios(id),
    fecha_actualizacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_empleados_estado_laboral ON empleados(estado_laboral);
CREATE INDEX IF NOT EXISTS idx_asignaciones_empleado_actual ON asignaciones_laborales(id_empleado, es_actual);
CREATE INDEX IF NOT EXISTS idx_movimientos_empleado_fecha ON movimientos_laborales(id_empleado, fecha_movimiento DESC);
CREATE INDEX IF NOT EXISTS idx_eval_desempeno_periodo ON evaluaciones_desempeno(periodo, fecha_evaluacion DESC);
CREATE INDEX IF NOT EXISTS idx_novedades_estado ON novedades_disciplinarias(estado, fecha_registro DESC);
CREATE INDEX IF NOT EXISTS idx_eventos_laborales_empleado ON eventos_laborales(id_empleado, fecha_evento DESC);

INSERT INTO sedes (codigo, nombre, ciudad, direccion)
VALUES ('PRINCIPAL', 'Sede Principal', 'N/D', 'N/D')
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO cargos (codigo, nombre, area, nivel)
VALUES
    ('ANL-SYS', 'Analista de Sistemas', 'Tecnología', 'Profesional'),
    ('JEF-OPS', 'Jefe de Operaciones', 'Operaciones', 'Jefatura')
ON CONFLICT (codigo) DO NOTHING;

INSERT INTO plantillas_desempeno_cargo (id_cargo, nombre, version, criterios_json, activa)
SELECT
    c.id,
    'Desempeño base Analista de Sistemas',
    1,
    '[{"id":"mantenimientos","texto":"Cumplimiento de mantenimientos planificados","peso":4,"max":10},{"id":"tickets","texto":"Resolución de tickets del área","peso":3,"max":10},{"id":"documentacion","texto":"Documentación técnica y reportes","peso":3,"max":10}]',
    TRUE
FROM cargos c
WHERE c.codigo = 'ANL-SYS'
ON CONFLICT (id_cargo, nombre, version) DO NOTHING;

INSERT INTO configuracion_tema (id, nombre, logo_texto)
VALUES (1, 'Tema corporativo', 'TalentFlow')
ON CONFLICT (id) DO NOTHING;
