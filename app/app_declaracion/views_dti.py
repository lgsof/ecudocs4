
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy

from app_declaracion.models_docdti import Declaracion
from app_docs.views_docs import EcuapassDocDetailView

#--------------------------------------------------------------------
#--------------------------------------------------------------------
# Decorador personalizado para requerir autenticación en una vista basada en clase
def login_required_class (view_func):
	return method_decorator (login_required, name='dispatch') (view_func)

#--------------------------------------------------------------------
#-- Declaracion
#--------------------------------------------------------------------

class DeclaracionListView (generic.ListView):
	model = Declaracion

class DeclaracionDetailView (EcuapassDocDetailView):
	model = Declaracion

class DeclaracionCreate (login_required_class (CreateView)):
	model = Declaracion
	fields = '__all__'
	#fields = ['tipo','remitente','destinatario','fecha_emision']

class DeclaracionUpdate (login_required_class (UpdateView)):
	model = Declaracion
	fields = '__all__'
	#fields = ['tipo','remitente','destinatario','fecha_emision']

class DeclaracionDelete (login_required_class (DeleteView)):
	model = Declaracion
	success_url = reverse_lazy ('declaracion-listado')

