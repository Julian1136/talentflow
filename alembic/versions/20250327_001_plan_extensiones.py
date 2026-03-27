"""Extensiones plan TalentFlow + cola reintentos correo

Revision ID: 20250327_001
Revises:
Create Date: 2025-03-27
"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20250327_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE aplicaciones ADD COLUMN IF NOT EXISTS analisis_ia_text TEXT")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notas_internas_aplicacion (
            id SERIAL PRIMARY KEY,
            id_aplicacion INTEGER NOT NULL REFERENCES aplicaciones(id) ON DELETE CASCADE,
            id_usuario INTEGER REFERENCES usuarios(id),
            cuerpo TEXT NOT NULL,
            fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_notas_internas_aplicacion ON notas_internas_aplicacion(id_aplicacion)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tareas_onboarding_empleado (
            id SERIAL PRIMARY KEY,
            id_empleado INTEGER NOT NULL REFERENCES empleados(id) ON DELETE CASCADE,
            titulo VARCHAR(200) NOT NULL,
            hecha BOOLEAN DEFAULT FALSE,
            orden INTEGER DEFAULT 0,
            fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tareas_onboarding_empleado ON tareas_onboarding_empleado(id_empleado)"
    )
    op.execute(
        "ALTER TABLE entrevistas ADD COLUMN IF NOT EXISTS recordatorio_enviado_en TIMESTAMP WITHOUT TIME ZONE"
    )
    op.execute(
        """
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
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_correo_cola_proximo ON correo_cola_reintento(proximo_intento_en)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_correo_cola_proximo")
    op.execute("DROP TABLE IF EXISTS correo_cola_reintento")
    op.execute("ALTER TABLE entrevistas DROP COLUMN IF EXISTS recordatorio_enviado_en")
    op.execute("DROP TABLE IF EXISTS tareas_onboarding_empleado")
    op.execute("DROP TABLE IF EXISTS notas_internas_aplicacion")
    op.execute("ALTER TABLE aplicaciones DROP COLUMN IF EXISTS analisis_ia_text")
