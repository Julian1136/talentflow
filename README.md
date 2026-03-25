# TalentFlow

Aplicación Flask para gestión de selección de candidatos.

## Requisitos

- Windows 10/11
- PostgreSQL 13+ en ejecución
- Python 3.10+ instalado y disponible en `PATH`

## 1) Configurar entorno Python

```powershell
cd C:\xampp\htdocs\talentflow
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Configurar variables de entorno

Crear `.env` a partir de `.env.example` (en la **raíz del proyecto**, codificación **UTF-8**):

```powershell
Copy-Item .env.example .env
```

No incluyas el archivo `.env` en el control de versiones (contiene secretos).

La aplicación carga siempre `.env` desde la carpeta donde está `app.py` (no depende del directorio de trabajo). Para usar otra ruta: variable de entorno del sistema `DOTENV_PATH`.

Variables importantes:

- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`: conexión de la app.
- `DB_ADMIN_USER`, `DB_ADMIN_PASSWORD`, `DB_ADMIN_DB`: usuario administrador de PostgreSQL para crear rol/base (solo usadas por `setup_db.py`).
- `SECRET_KEY`: clave de sesión Flask (en producción debe ser larga y aleatoria; con `FLASK_ENV=production` se advierte si sigue el valor por defecto).
- `FLASK_DEBUG`, `FLASK_RUN_PORT`: modo desarrollo y puerto al ejecutar `python app.py`.
- `FLASK_RUN_HOST`: por defecto `127.0.0.1` (solo tu PC). Pon `0.0.0.0` en `.env` para acceder desde la LAN (`http://<IP-del-servidor>:5000`). **Importante:** esa variable solo la usa `python app.py`. Si arrancas con `flask run`, el CLI ignora `FLASK_RUN_HOST` y queda en `127.0.0.1`; en ese caso usa `flask run --host=0.0.0.0` o el perfil *TalentFlow: flask run en LAN* en `.vscode/launch.json`. Comprueba con `netstat -ano | findstr :5000`: debe aparecer `0.0.0.0:5000`, no solo `127.0.0.1:5000`. Abre el puerto en el firewall de Windows si hace falta. El servidor de desarrollo no es adecuado para producción pública.
- `UPLOAD_FOLDER`, `MAX_CONTENT_LENGTH_MB`: adjuntos.
- `MAIL_*`: correo saliente (opcional; sin `MAIL_USERNAME` no se envían notificaciones).
- `ENABLE_SCHEDULER`: `True` para activar APScheduler (tareas en segundo plano; requiere dependencia instalada).
- `ANTHROPIC_API_KEY`: opcional, para análisis de compatibilidad con IA (fase 3).

Tras cambios de esquema SQL nuevos (p. ej. plantillas de evaluación), ejecuta manualmente los scripts añadidos en `database/` o aplícalos en pgAdmin.

## 3) Inicializar PostgreSQL con scripts SQL

Este paso ejecuta en orden:

1. `database/00_init_role_db.sql`
2. `database/01_schema.sql`
3. `database/02_seed.sql`

```powershell
python setup_db.py
```

Si tu instalación de Python expone `py` en vez de `python`, usa:

```powershell
py setup_db.py
```

## 4) Ejecutar la aplicación

```powershell
python app.py
```

La app quedará disponible en:

- [http://localhost:5000](http://localhost:5000)

## Usuario inicial (seed)

- Correo: `admin@empresa.com`
- Contraseña: `Admin123!`

## Checklist de prueba rápida

1. Abrir `/auth/login` e iniciar sesión con admin.
2. Verificar carga de dashboard (`/dashboard`).
3. Ir a **Candidatos** y crear un candidato.
4. Ir a **Vacantes** y crear una vacante.
5. Aplicar candidato a vacante desde detalle de candidato.
6. Revisar detalle de proceso (`/proceso/<id_aplicacion>`).
7. Abrir **Reportes** y exportar CSV.
8. (Opcional) Portal público: `/p/vacante/<id>` para postular sin login (vacante abierta).

## Estructura DB relevante

- `database/00_init_role_db.sql`: rol/app user y base de datos.
- `database/01_schema.sql`: tablas, constraints, índices.
- `database/02_seed.sql`: datos semilla (roles + admin).
- `database/03_plantillas_evaluacion.sql`: plantillas de evaluación dinámica y tabla de respuestas.
- `database/04_aplicacion_score.sql`: columna `score` en aplicaciones.
- `database/05_firma_aceptaciones.sql`: registro de aceptaciones simuladas.
- `database/CALENDARIO_DECISION.md`: decisión de diseño del calendario (sin slots).

Ejecuta los scripts 03–05 en PostgreSQL (pgAdmin o `psql`) cuando actualices un entorno existente.

## Notas operativas

- El proyecto no usa migraciones automáticas; el esquema oficial está en scripts SQL.
- `setup_db.py` es idempotente: se puede re-ejecutar sin duplicar datos semilla.
