# app_usuarios/management/commands/list_empresas.py
from django.core.management.base import BaseCommand
from app_usuarios.models import Empresa

class Command (BaseCommand):
    help = "Lista todas las empresas  (empresas) registradas en el sistema."

    def handle (self, *args, **options):
        empresas = Empresa.objects.all ().order_by ("nickname")
        if not empresas.exists ():
            self.stdout.write (self.style.WARNING ("No hay empresas registradas."))
            return

        self.stdout.write (self.style.MIGRATE_HEADING ("Empresas registradas:\n"))
        for e in empresas:
            estado = "Activo" if e.activo else "Inactivo"
            self.stdout.write (
                f" - {e.nickname:15} | {e.nombre:30} | {estado:8} | creado: {e.fecha_creacion.strftime ('%Y-%m-%d %H:%M')}"
            )

#-------- USAGE ----------------
# 3) Uso en consola
# python manage.py list_empresas
# 
# 4) Ejemplo de salida
# Empresas registradas:
# 
#  - byza            | BYZA S.A.                   | Activo   | creado: 2025-08-15 12:55
#  - nta             | NTA Ltda                    | Inactivo | creado: 2025-08-15 13:10
#  - logitrans       | Logitrans Transporte        | Activo   | creado: 2025-08-15 13:22


