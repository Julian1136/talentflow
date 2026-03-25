-- Ejecutar conectado a la base talentflow_db.
-- Datos base del sistema (idempotente).

INSERT INTO roles (nombre, descripcion)
VALUES
    ('administrador', 'Rol de administrador'),
    ('reclutador', 'Rol de reclutador'),
    ('psicologo', 'Rol de psicologo'),
    ('jefe_area', 'Rol de jefe de area')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO usuarios (
    cedula,
    nombres,
    apellidos,
    correo,
    password_hash,
    id_rol,
    activo
)
SELECT
    '1234567890',
    'Admin',
    'Sistema',
    'admin@empresa.com',
    crypt('Admin123!', gen_salt('bf')),
    r.id,
    TRUE
FROM roles r
WHERE r.nombre = 'administrador'
ON CONFLICT (correo) DO NOTHING;
