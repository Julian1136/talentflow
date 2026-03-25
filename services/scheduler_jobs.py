"""
Jobs de APScheduler (opcional). Active con ENABLE_SCHEDULER=True en .env.

Ejemplos futuros: recordatorio 24h antes de entrevista, reintento de correos.
"""


def register_scheduler_jobs(scheduler, app):
    """Registra tareas en el scheduler; se ejecuta dentro de create_app."""
    # Placeholder: añadir jobs con scheduler.add_job(...)
    _ = (scheduler, app)
