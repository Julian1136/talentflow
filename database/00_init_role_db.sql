-- Ejecutar conectado a la base "postgres" con un usuario administrador.
-- Crea rol de aplicación y base de datos si no existen.
-- Variables esperadas por setup_db.py:
--   __DB_USER__
--   __DB_PASSWORD__
--   __DB_NAME__

DO
$$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '__DB_USER__') THEN
        EXECUTE format(
            'CREATE ROLE %I LOGIN PASSWORD %L',
            '__DB_USER__',
            '__DB_PASSWORD__'
        );
    END IF;
END
$$;

