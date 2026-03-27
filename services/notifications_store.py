"""
Persistencia ligera de notificaciones vistas por usuario.
"""
from __future__ import annotations

from sqlalchemy import text

from extensions import db


def ensure_table() -> None:
    db.session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS notificaciones_vistas (
                id SERIAL PRIMARY KEY,
                id_usuario INTEGER NOT NULL REFERENCES usuarios(id),
                notif_key VARCHAR(200) NOT NULL,
                fecha_vista TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                CONSTRAINT uq_notif_vista UNIQUE(id_usuario, notif_key)
            )
            """
        )
    )
    db.session.commit()


def was_seen(user_id: int, notif_key: str) -> bool:
    ensure_table()
    row = db.session.execute(
        text("SELECT 1 FROM notificaciones_vistas WHERE id_usuario=:uid AND notif_key=:k LIMIT 1"),
        {"uid": user_id, "k": notif_key},
    ).first()
    return row is not None


def mark_seen(user_id: int, notif_key: str) -> None:
    ensure_table()
    db.session.execute(
        text(
            """
            INSERT INTO notificaciones_vistas(id_usuario, notif_key)
            VALUES (:uid, :k)
            ON CONFLICT (id_usuario, notif_key) DO NOTHING
            """
        ),
        {"uid": user_id, "k": notif_key},
    )
    db.session.commit()


def mark_many_seen(user_id: int, notif_keys: list[str]) -> int:
    """Marca varias notificaciones como vistas. Retorna cuántas recibió."""
    ensure_table()
    keys = [k.strip() for k in notif_keys if k and str(k).strip()]
    if not keys:
        return 0
    for k in keys:
        db.session.execute(
            text(
                """
                INSERT INTO notificaciones_vistas(id_usuario, notif_key)
                VALUES (:uid, :k)
                ON CONFLICT (id_usuario, notif_key) DO NOTHING
                """
            ),
            {"uid": user_id, "k": k},
        )
    db.session.commit()
    return len(keys)
