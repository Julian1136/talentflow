-- Registro de aceptación simulada de documentos (contrato, oferta, etc.).
CREATE TABLE IF NOT EXISTS firma_aceptaciones (
    id SERIAL PRIMARY KEY,
    token VARCHAR(96) UNIQUE NOT NULL,
    id_aplicacion INTEGER REFERENCES aplicaciones(id) ON DELETE SET NULL,
    cedula_candidato VARCHAR(20) REFERENCES candidatos(cedula) ON DELETE SET NULL,
    tipo_documento VARCHAR(100),
    hash_documento VARCHAR(128),
    ip_aceptacion VARCHAR(64),
    user_agent TEXT,
    fecha_aceptacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_firma_token ON firma_aceptaciones(token);
