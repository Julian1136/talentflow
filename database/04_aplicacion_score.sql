-- Puntuación sugerida candidato vs vacante (calculada en app).
ALTER TABLE aplicaciones ADD COLUMN IF NOT EXISTS score NUMERIC(5, 2);
