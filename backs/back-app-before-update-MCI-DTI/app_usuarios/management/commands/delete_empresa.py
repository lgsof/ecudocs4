# app_usuarios/management/commands/delete_empresa.py
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from app_usuarios.models import Empresa

class Command(BaseCommand):
    help = (
        "Desactiva o elimina una Empresa (empresa) por su código.\n"
        "Por defecto realiza soft-delete (activo=False). Use --hard para borrar definitivamente."
    )

    def add_arguments(self, parser):
        parser.add_argument("nickname", type=str, help="Código/subdominio del empresa (p.ej. 'byza').")
        parser.add_argument(
            "--hard",
            action="store_true",
            help="Eliminar definitivamente (DELETE). Por defecto sólo desactiva (soft-delete)."
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="No pedir confirmación interactiva."
        )

    def _related_counts(self, empresa: Empresa):
        """
        Retorna un dict {rel_name: count} con cantidades de objetos relacionados.
        Útil para mostrar el impacto antes de un borrado duro.
        """
        counts = {}
        for field in empresa._meta.get_fields():
            # Solo relaciones hacia otros modelos, creadas automáticamente por Django
            if (field.one_to_many or field.one_to_one or field.many_to_many) and field.auto_created:
                rel_name = field.get_accessor_name()
                try:
                    manager = getattr(empresa, rel_name)
                    # many_to_many y one_to_many tienen .all()
                    counts[rel_name] = manager.all().count()
                except Exception:
                    # relaciones OneToOne pueden no existir
                    try:
                        obj = getattr(empresa, rel_name, None)
                        counts[rel_name] = 1 if obj else 0
                    except Exception:
                        pass
        return counts

    def handle(self, *args, **opts):
        nickname = opts["nickname"].strip().lower()
        hard   = opts["hard"]
        assume_yes = opts["yes"]

        try:
            empresa = Empresa.objects.get(nickname=nickname)
        except Empresa.DoesNotExist:
            raise CommandError(f"No existe empresa con código '{nickname}'.")

        if not hard:
            # Soft-delete (recomendado)
            if not empresa.activo:
                self.stdout.write(self.style.WARNING(f"'{nickname}' ya estaba inactiva."))
                return
            empresa.activo = False
            empresa.save(update_fields=["activo"])
            self.stdout.write(self.style.SUCCESS(f"Empresa '{nickname}' desactivada (soft-delete)."))
            return

        # Hard delete: mostrar recuento de relaciones
        rel_counts = self._related_counts(empresa)
        total_rel = sum(rel_counts.values())

        # Mensaje previo
        self.stdout.write(self.style.MIGRATE_HEADING("Vas a ELIMINAR definitivamente el empresa:\n"))
        self.stdout.write(f" - código: {empresa.nickname}\n - nombre: {empresa.nombre}")
        if rel_counts:
            self.stdout.write("\nObjetos relacionados (conteo aproximado):")
            for rel, cnt in sorted(rel_counts.items()):
                self.stdout.write(f"   • {rel}: {cnt}")
        self.stdout.write("")

        # Confirmación
        if not assume_yes:
            esperado = f"DELETE {nickname}"
            self.stdout.write(self.style.WARNING(
                f"Esta acción es IRREVERSIBLE. Escribe exactamente: {esperado}"
            ))
            respuesta = input("> ").strip()
            if respuesta != esperado:
                raise CommandError("Operación cancelada por el usuario.")

        # Eliminar en transacción
        with transaction.atomic():
            empresa.delete()

        resumen = " (con objetos relacionados)" if total_rel > 0 else ""
        self.stdout.write(self.style.SUCCESS(f"Empresa '{nickname}' eliminada definitivamente{resumen}."))

#------------ USAGE
# # Soft-delete (recomendado): desactiva el empresa
# python manage.py delete_empresa byza
# 
# # Hard delete: elimina definitivamente (pide confirmación)
# python manage.py delete_empresa byza --hard
# 
# # Hard delete sin prompt (automatizaciones/CI, ÚSALO CON CUIDADO)
# python manage.py delete_empresa byza --hard --yes

