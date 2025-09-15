# app_usuarios/management/commands/create_empresa.py
from django.core.management.base import BaseCommand, CommandError
from app_usuarios.models import Empresa

class Command(BaseCommand):
    help = "Crea una nueva Empresa (empresa) identificada por su código (subdominio)."

    def add_arguments(self, parser):
        parser.add_argument("nickname", type=str, help="Código/subdominio de la empresa (ej: 'byza').")
        parser.add_argument("--nombre", type=str, required=True, help="Nombre completo de la empresa.")
        parser.add_argument("--inactiva", action="store_true", help="Crear empresa inicialmente inactiva.")

    def handle(self, *args, **options):
        nickname = options["nickname"].strip().lower()
        nombre = options["nombre"].strip()
        activo = not options["inactiva"]

        if Empresa.objects.filter(nickname=nickname).exists():
            raise CommandError(f"La empresa con código '{nickname}' ya existe.")

        empresa = Empresa.objects.create(
            nickname=nickname,
            nombre=nombre,
            activo=activo,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Empresa creada: {empresa.nombre} (subdominio '{empresa.nickname}', activo={empresa.activo})"
            )
        )

#----------- USAGE desde consola:
# Crear una empresa activa con código 'byza'
# python manage.py create_empresa byza --nombre "BYZA S.A."
# Output: Empresa creada: BYZA S.A. (subdominio 'byza', activo=True)

# Crear una empresa inicialmente inactiva
# python manage.py create_empresa nta --nombre "NTA Ltda" --inactiva

