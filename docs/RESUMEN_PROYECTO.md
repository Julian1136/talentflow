# TalentFlow — Resumen del proyecto (estado actual)

Documento orientado a **qué hace hoy** la aplicación: alcance funcional, módulos, datos y servicios auxiliares. No sustituye el `README.md` ni la guía de despliegue.

---

## 1. Propósito

**TalentFlow** es una **plataforma web de gestión de selección de personal**: registro de candidatos y vacantes, postulaciones (aplicaciones), seguimiento del proceso por **estados**, entrevistas, evaluaciones, métricas en dashboard, kanban, calendario, correos opcionales, portal público de postulación y utilidades de scoring y compatibilidad con IA (cuando hay API key).

---

## 2. Stack técnico

| Área | Tecnología |
|------|------------|
| Framework | Flask |
| ORM / BD | SQLAlchemy 2.x, **PostgreSQL** |
| Driver | En Windows: **psycopg 3** (`postgresql+psycopg`); en otros SO: **psycopg2** con `client_encoding=UTF8` |
| Autenticación | Flask-Login |
| Correo | Flask-Mail (desactivado de facto si `MAIL_USERNAME` está vacío) |
| Tareas en background | **APScheduler** opcional (`ENABLE_SCHEDULER=True`; jobs registrados pero aún placeholder) |
| Front (vistas) | Jinja2 + HTML/CSS propios; **Chart.js** en dashboard; **FullCalendar** en calendario |

Variables de entorno: raíz del proyecto en `.env` (UTF-8 recomendado en Windows). Referencia ampliada en `.env.example` y `README.md`.

---

## 3. Roles de usuario

Definidos en tabla `roles` y asociados a `usuarios`:

- **administrador**: acceso amplio; bloque de **alertas de sesgo** en dashboard y gestión de usuarios.
- **reclutador**: candidatos, vacantes, proceso, kanban, calendario, aplicar candidatos a vacantes, etc.
- **psicólogo**: orientado a evaluaciones psicológicas en el flujo (según permisos en vistas).

Las propiedades `es_admin`, `es_reclutador` y `es_psicologo` en el modelo `Usuario` condicionan parte de la UI y rutas.

**Contraseñas**: el modelo acepta hash **Werkzeug** (pbkdf2) y **bcrypt** (semillas SQL tipo pgcrypto), para convivir con datos creados por scripts.

---

## 4. Dominio de datos (modelos principales)

- **Rol / Usuario**: cuentas internas del sistema.
- **Candidato** (PK: `cedula`): datos personales, ciudad, fuente de captación, etc.
- **HojaDeVida**: experiencia, formación (JSON), habilidades, idiomas, resumen (1:1 con candidato).
- **Vacante**: título, descripción, área, ciudad, salario, requisitos, estado (`abierta` / cierre), responsable.
- **Aplicacion**: relación candidato–vacante **única** por par; **estado** del embudo; **score** numérico (scoring automático); fecha de aplicación.
- **Contacto**, **Entrevista**, **EvaluacionPsicologica**, **EvaluacionTecnica**: hitos del proceso ligados a la aplicación.
- **PlantillaEvaluacion** / **EvaluacionPlantillaRespuesta**: criterios en JSON y respuestas puntuadas por aplicación.
- **DocumentoAdjunto**: archivos subidos (disc) con metadatos.
- **HistorialProceso**: auditoría de acciones y cambios de estado.
- **FirmaAceptacion**: registro de aceptación vía **token** (firma electrónica simulada).

**Estados de aplicación** (orden lógico del proceso): desde `hoja_de_vida_recibida` hasta `contratado` / `rechazado`, definidos en `ESTADOS_APLICACION` en `models.py`.

---

## 5. Scripts SQL (base de datos)

En `database/`, ejecutar en orden según necesidad de instalación:

1. `00_init_role_db.sql` — rol y base (según entorno).
2. `01_schema.sql` — esquema principal.
3. `02_seed.sql` — datos iniciales (roles, usuario admin, etc.).
4. `03_plantillas_evaluacion.sql` — tablas de plantillas y respuestas.
5. `04_aplicacion_score.sql` — columna `score` en `aplicaciones`.
6. `05_firma_aceptaciones.sql` — tabla de firmas.

Existe nota de diseño en `database/CALENDARIO_DECISION.md` (calendario basado en entrevistas, sin tabla de “slots” separada).

---

## 6. Módulos y rutas (blueprints)

Prefijos aproximados; siempre verificar con `url_for` en plantillas.

### 6.1 Autenticación (`/auth`)

- Login / logout.
- Listado y alta de **usuarios** (según política del controlador).

### 6.2 Dashboard y reportes

- **`/` y `/dashboard`**: KPIs, distribución por estado, actividad reciente, gráficos **Chart.js** (embudo, conversión por vacante, tiempo por etapa vía APIs JSON).
- **APIs JSON** (sesión requerida): `/dashboard/api/embudo`, `/dashboard/api/conversion-vacante`, `/dashboard/api/tiempo-etapa`.
- **Admin**: `/dashboard/api/sesgos` — alertas de posible sesgo por rechazos y ciudad.
- **`/reportes`**: vista de reportes y **exportación CSV** de candidatos (`/reportes/exportar-candidatos`).

### 6.3 Candidatos (`/candidatos`)

- Listado, **nuevo** candidato, **detalle**, **editar**.
- **Expediente** agregado (vista dedicada).
- Subida de **documentos** y **descarga** por id.
- **Aplicar a vacante** (POST): crea `Aplicacion`, historial y calcula **score** si el servicio de scoring está operativo.

### 6.4 Vacantes (`/vacantes`)

- Listado, **nueva**, detalle, **cerrar** vacante.

### 6.5 Proceso de selección (`/proceso`)

Vista detallada por **id de aplicación** (`/proceso/<app_id>`) con pestañas / acciones típicas:

- Cambio de **estado**.
- Registro de **contacto**.
- **Entrevista** (programación / datos) y **resultado** de entrevista por id de entrevista.
- **Evaluación psicológica** y **prueba técnica**.
- **Evaluación por plantilla** (criterios JSON).
- **Compatibilidad IA** (POST): usa servicio Anthropic si está configurado.

Integración con **correos** donde corresponda (entrevistas, recordatorios, etc.) vía `services/email_service.py`.

### 6.6 Kanban (`/kanban`)

- Tablero por columnas de estado.
- **Mover** tarjeta (cambio de estado).
- API **columna** por estado (JSON) y **stats**.

### 6.7 Calendario (`/calendario`)

- Vista FullCalendar.
- **Eventos** JSON para el calendario.
- **Programar** entrevista (POST).
- **Resultado** de entrevista desde flujo de calendario (POST).

### 6.8 Firma (`/firma`)

- **`/firma/aceptar/<token>`** (GET/POST): pantalla pública o semi-pública para aceptar documento; valida token en `FirmaAceptacion`.
- **`/firma/preparar/<app_id>`** (POST, sesión): genera enlace/token de aceptación para una aplicación.

### 6.9 Portal público (`/p`) — sin login

- **`/p/vacante/<id>`**: ficha de vacante abierta.
- **`/p/vacante/<id>/postular`**: crea o actualiza candidato, crea aplicación, historial y scoring; redirección con mensajes flash.

---

## 7. Servicios (`services/`)

| Servicio | Función |
|----------|---------|
| `email_service.py` | Inicialización Flask-Mail, plantillas HTML de correos, funciones de envío (notificaciones de proceso, entrevistas, etc.). |
| `scoring.py` | Cálculo de **score** de una aplicación (alineación candidato–vacante según reglas del proyecto). |
| `cv_parser.py` | Extracción / parseo de CV (PDF u otros) para enriquecer datos cuando se usa en el flujo. |
| `anthropic_match.py` | Análisis de **compatibilidad** candidato–vacante vía API **Anthropic** (requiere clave en entorno). |
| `scheduler_jobs.py` | Registro de jobs APScheduler; hoy es **extensible** (sin tareas programadas concretas obligatorias). |

---

## 8. Archivos estáticos y subidas

- **`UPLOAD_FOLDER`**: por defecto bajo el proyecto (`uploads/candidatos` o variante); límite de tamaño configurable (`MAX_CONTENT_LENGTH_MB`).
- **`static/`**: CSS, JS, assets del tema.

---

## 9. Arranque

- Punto de entrada: **`app.py`** — `create_app()` registra extensiones, blueprints y scheduler condicional.
- Ejecución local típica: `python app.py` (puerto y debug según `get_flask_run_config()` / `.env`).
- Utilidad de base: **`setup_db.py`** (si existe en el repo) para alinear rol/contraseña y scripts iniciales según documentación del README.

---

## 10. Limitaciones y matices útiles

- **Correos**: sin `MAIL_USERNAME` (y credenciales SMTP) los envíos no tienen efecto útil; la app puede arrancar igual.
- **IA**: endpoints de compatibilidad dependen de **ANTHROPIC_API_KEY** (o variables que use el servicio).
- **Scheduler**: al activarse, no ejecuta aún lógica de negocio pesada hasta añadir jobs en `scheduler_jobs.py`.
- **PostgreSQL** es estricto con tipos: formularios que envían números como texto deben convertirse a `int` en el controlador (p. ej. `id_vacante` al aplicar a vacante).

---

## 11. Mapa rápido de carpetas

```
app.py, config.py, extensions.py, models.py
controllers/     # Blueprints y vistas
templates/       # Jinja2 por módulo
services/        # Email, scoring, CV, IA, scheduler
database/        # SQL y notas
static/          # Recursos front
uploads/         # Documentos (configurable)
docs/            # Documentación ad hoc (este archivo)
```

---

*Última actualización del contenido: alineado con la estructura actual del repositorio (módulos y modelos descritos arriba).*
