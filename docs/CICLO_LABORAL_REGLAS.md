# Reglas del ciclo laboral

## Estados macro

- `candidato`: perfil en reclutamiento.
- `pre_ingreso`: aceptación inicial pendiente (documentación, onboarding).
- `activo`: empleado en operación.
- `suspendido`: empleado activo con medida temporal.
- `retiro`: salida voluntaria o fin de contrato.
- `despedido`: salida disciplinaria / terminación por causa.

## Eventos trazables

- Contratación desde `Aplicacion`.
- Asignación inicial de cargo, sede y jefe.
- Movimientos: ascenso, traslado, cambio de sede, cambio de cargo, cambio de jefe, ajuste salarial.
- Evaluación de desempeño: registro por jefe y aceptación/rechazo del empleado.
- Disciplina: falta, severidad, sanción, aprobación.
- Desvinculación: tipo, causa, fecha efectiva y documento.

## Permisos por rol

- `administrador`: acceso total.
- `rrhh`/`reclutador`: administración de ciclo laboral y reportes HR.
- `jefe_area`: puede participar como evaluador de desempeño.
- `empleado` (si se asocia `id_usuario`): consulta su expediente y responde evaluación.

## Integridad de datos

- Una sola asignación laboral activa (`es_actual=true`) por empleado.
- Cada movimiento laboral debe dejar rastro en `eventos_laborales`.
- La salida (`retiro`/`despedido`) cierra la asignación vigente y registra `desvinculaciones`.
