from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model ()

class Command (BaseCommand):
    help = "Create a new user"

    def add_arguments (self, parser):
        parser.add_argument ('username', type=str, help='Username for the new user')
        parser.add_argument ('email', type=str, help='Email address for the new user')
        parser.add_argument ('password', type=str, help='Password for the new user')
        parser.add_argument ('--perfil', type=str, default='funcionario', help='Perfil: externo, funcionario, director')
        parser.add_argument ('--pais', type=str, default='COLOMBIA', help='Pais: ECUADOR, COLOMBIA, PERU, TODOS')
        parser.add_argument ('--empresa', type=int, default=None, help='ID of Empresa  (optional)')

    def handle (self, *args, **options):
        username = options['username']
        email    = options['email']
        password = options['password']
        perfil   = options['perfil']
        pais     = options['pais']
        empresa  = options['empresa']

        if User.objects.filter (username=username).exists ():
            raise CommandError (f"User '{username}' already exists")

        user = User.objects.create_user (
            username=username,
            email=email,
            password=password,
            perfil=perfil,
            pais=pais,
            empresa_id=empresa,
        )

        self.stdout.write (self.style.SUCCESS (f"User '{user.username}' created successfully"))

