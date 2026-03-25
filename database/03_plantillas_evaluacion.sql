-- Ejecutar conectado a talentflow_db (después de 01_schema.sql).
-- Plantillas de evaluación dinámicas y respuestas por aplicación.

CREATE TABLE IF NOT EXISTS plantillas_evaluacion (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    criterios_json TEXT NOT NULL,
    activa BOOLEAN DEFAULT TRUE,
    fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evaluaciones_plantilla_respuestas (
    id SERIAL PRIMARY KEY,
    id_aplicacion INTEGER NOT NULL REFERENCES aplicaciones(id) ON DELETE CASCADE,
    id_plantilla INTEGER NOT NULL REFERENCES plantillas_evaluacion(id) ON DELETE CASCADE,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id),
    respuestas_json TEXT NOT NULL,
    puntaje_total NUMERIC(6, 2),
    fecha_registro TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_eval_plantilla_aplicacion ON evaluaciones_plantilla_respuestas(id_aplicacion);
CREATE INDEX IF NOT EXISTS idx_eval_plantilla_plantilla ON evaluaciones_plantilla_respuestas(id_plantilla);

INSERT INTO plantillas_evaluacion (nombre, criterios_json, activa)
SELECT
    'Entrevista estándar RRHH',
    '[{"id":"comunicacion","texto":"Comunicación y claridad","peso":1,"max":5},{"id":"tecnico","texto":"Conocimiento técnico del cargo","peso":2,"max":5},{"id":"actitud","texto":"Actitud y ajuste cultural","peso":1,"max":5}]',
    TRUE
WHERE NOT EXISTS (SELECT 1 FROM plantillas_evaluacion WHERE nombre = 'Entrevista estándar RRHH');
