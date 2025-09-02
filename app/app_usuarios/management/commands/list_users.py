from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = "List all users"

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa',
            type=int,
            help='Filter users by empresa ID'
        )
        parser.add_argument(
            '--perfil',
            type=str,
            help='Filter users by perfil (externo, funcionario, director)'
        )
        parser.add_argument(
            '--pais',
            type=str,
            help='Filter users by pais (ECUADOR, COLOMBIA, PERU, TODOS)'
        )

    def handle(self, *args, **options):
        qs = User.objects.all().select_related('empresa')

        if options['empresa']:
            qs = qs.filter(empresa_id=options['empresa'])
        if options['perfil']:
            qs = qs.filter(perfil=options['perfil'])
        if options['pais']:
            qs = qs.filter(pais=options['pais'])

        if not qs.exists():
            self.stdout.write(self.style.WARNING("No users found"))
            return

        # Table header
        header = f"{'ID':<4} {'Username':<15} {'Email':<30} {'Perfil':<12} {'Pais':<10} {'Empresa':<20}"
        self.stdout.write(header)
        self.stdout.write("-" * len(header))

        # Rows
        for u in qs:
            empresa_name = u.empresa.nombre if u.empresa else "-"
            line = f"{u.id:<4} {u.username:<15} {u.email:<30} {u.perfil:<12} {u.pais:<10} {empresa_name:<20}"
            self.stdout.write(line)

