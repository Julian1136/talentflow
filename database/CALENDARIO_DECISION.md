# Decisión: calendario de entrevistas

**Estado elegido:** el sistema usa el modelo existente `Entrevista` con fechas concretas y la vista FullCalendar en `/calendario`, sin tabla de `SlotEntrevista`.

**Motivo:** cubre el caso de uso principal (agendar y reprogramar citas con notificación por correo) con menos complejidad que gestionar disponibilidad por bloques, solapes y confirmación de slot.

**Cuándo reconsiderar:** si RRHH necesita que los candidatos elijan entre franjas publicadas por entrevistador, habría que añadir modelo de slots, API de disponibilidad y flujo de reserva.
