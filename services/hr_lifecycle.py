"""
Reglas de ciclo laboral y utilidades de trazabilidad.
"""
from __future__ import annotations

import json
from datetime import date, datetime

from extensions import db
from models import (
    Aplicacion,
    AsignacionLaboral,
    Cargo,
    Empleado,
    EventoLaboral,
    MovimientoLaboral,
    Sede,
)


def registrar_evento_laboral(empleado: Empleado, tipo: str, descripcion: str, usuario_id: int | None, metadata: dict | None = None) -> None:
    ev = EventoLaboral(
        id_empleado=empleado.id,
        tipo_evento=tipo,
        descripcion=descripcion[:200],
        id_usuario=usuario_id,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
        fecha_evento=datetime.utcnow(),
    )
    db.session.add(ev)


def asegurar_catalogos_hr() -> tuple[Sede, Cargo]:
    sede = Sede.query.filter_by(codigo="PRINCIPAL").first()
    if not sede:
        sede = Sede(codigo="PRINCIPAL", nombre="Sede Principal", ciudad="N/D", direccion="N/D")
        db.session.add(sede)

    cargo = Cargo.query.filter_by(codigo="ANL-SYS").first()
    if not cargo:
        cargo = Cargo(codigo="ANL-SYS", nombre="Analista de Sistemas", area="Tecnología", nivel="Profesional")
        db.session.add(cargo)
    db.session.flush()
    return sede, cargo


def asegurar_empleado_por_contratacion(aplicacion: Aplicacion, usuario_id: int) -> Empleado:
    empleado = Empleado.query.filter_by(cedula=aplicacion.cedula_candidato).first()
    if empleado:
        if empleado.estado_laboral in ("retiro", "despedido"):
            empleado.estado_laboral = "activo"
            empleado.fecha_salida = None
            empleado.motivo_salida = None
        return empleado

    sede, cargo = asegurar_catalogos_hr()
    empleado = Empleado(
        cedula=aplicacion.cedula_candidato,
        id_aplicacion_origen=aplicacion.id,
        estado_laboral="activo",
        fecha_ingreso=date.today(),
    )
    db.session.add(empleado)
    db.session.flush()

    asignacion = AsignacionLaboral(
        id_empleado=empleado.id,
        id_cargo=cargo.id,
        id_sede=sede.id,
        id_jefe=usuario_id,
        fecha_inicio=date.today(),
        es_actual=True,
        observaciones="Asignación inicial generada al contratar.",
    )
    db.session.add(asignacion)
    db.session.flush()

    mov = MovimientoLaboral(
        id_empleado=empleado.id,
        tipo="ingreso",
        id_asignacion_nueva=asignacion.id,
        fecha_movimiento=date.today(),
        motivo=f"Ingreso desde aplicación #{aplicacion.id}",
        id_usuario=usuario_id,
    )
    db.session.add(mov)
    registrar_evento_laboral(
        empleado,
        "contratacion",
        "Empleado creado a partir de proceso de selección.",
        usuario_id,
        {"id_aplicacion": aplicacion.id},
    )
    return empleado
