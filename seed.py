#!/usr/bin/env python
"""
Seed inicial para TalentFlow.
Crea roles básicos y un usuario administrador.
"""
import os
import sys
from app import create_app
from extensions import db
from models import Rol, Usuario

app = create_app()
app.app_context().push()

def seed():
    # Crear roles
    roles = ['administrador', 'reclutador', 'psicologo', 'jefe_area']
    for nombre in roles:
        if not Rol.query.filter_by(nombre=nombre).first():
            rol = Rol(nombre=nombre, descripcion=f'Rol de {nombre}')
            db.session.add(rol)
    db.session.commit()

    # Crear usuario admin si no existe
    admin_role = Rol.query.filter_by(nombre='administrador').first()
    if admin_role and not Usuario.query.filter_by(correo='admin@empresa.com').first():
        admin = Usuario(
            cedula='1234567890',
            nombres='Admin',
            apellidos='Sistema',
            correo='admin@empresa.com',
            id_rol=admin_role.id,
            activo=True
        )
        admin.set_password('Admin123!')
        db.session.add(admin)
        db.session.commit()
        print("Usuario administrador creado: admin@empresa.com / Admin123!")
    else:
        print("El administrador ya existe o rol no encontrado.")

if __name__ == '__main__':
    seed()
