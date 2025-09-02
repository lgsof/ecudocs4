# tables.py
import django_tables2 as tables
from django_tables2.utils import A
from .models import Usuario

#----------------------------------------------------------
#----------------------------------------------------------
class UserTable(tables.Table):
	username = tables.LinkColumn ('actualizar', args=[A('pk')])  # Assuming 'actualizar' is your URL pattern name
	#email = tables.LinkColumn('user_email_detail', args=[A('pk')])

	# Columna adicional de "acciones" que se presenta al listar los usuarios
	columnaAcciones = tables.TemplateColumn(
		template_code='''
		<a href="{{ record.get_link_actualizar }}">Editar</a>,
		<a href="{{ record.get_link_eliminar }}">Eliminar</a>
		''',
		verbose_name='Acciones'
	)
	class Meta:
		model = Usuario
		template_name = "django_tables2/bootstrap4.html"
		fields = ("username", "email", "nombre", "pais", "perfil", "columnaAcciones")
		attrs = {'class': 'table table-striped table-bordered'}		

