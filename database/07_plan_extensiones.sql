-- Extensiones al plan TalentFlow (notas internas, IA guardada, onboarding).
-- Ejecutar en PostgreSQL sobre la base existente.

ALTER TABLE aplicaciones ADD COLUMN IF NOT EXISTS analisis_ia_text TEXT;

CREATE TABLE IF NOT EXISTS notas_internas_aplicacion (
    id SERIAL PRIMARY KEY,
    id_aplicacion INTEGER NOT NULL REFERENCES aplicaciones(id) ON DELETE CASCADE,
    id_usuario INTEGER REFERENCES usuarios(id),
    cuerpo TEXT NOT NULL,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_notas_internas_aplicacion ON notas_internas_aplicacion(id_aplicacion);

CREATE TABLE IF NOT EXISTS tareas_onboarding_empleado (
    id SERIAL PRIMARY KEY,
    id_empleado INTEGER NOT NULL REFERENCES empleados(id) ON DELETE CASCADE,
    titulo VARCHAR(200) NOT NULL,
    hecha BOOLEAN DEFAULT FALSE,
    orden INTEGER DEFAULT 0,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_tareas_onboarding_empleado ON tareas_onboarding_empleado(id_empleado);

ALTER TABLE entrevistas ADD COLUMN IF NOT EXISTS recordatorio_enviado_en TIMESTAMP WITHOUT TIME ZONE;

CREATE TABLE IF NOT EXISTS correo_cola_reintento (
    id SERIAL PRIMARY KEY,
    destinatario VARCHAR(255) NOT NULL,
    asunto VARCHAR(500) NOT NULL,
    cuerpo_html TEXT NOT NULL,
    intentos INTEGER DEFAULT 0,
    max_intentos INTEGER DEFAULT 5,
    ultimo_error TEXT,
    proximo_intento_en TIMESTAMP WITHOUT TIME ZONE,
    creado_en TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    enviado_en TIMESTAMP WITHOUT TIME ZONE
);

CREATE INDEX IF NOT EXISTS ix_correo_cola_proximo ON correo_cola_reintento(proximo_intento_en);
