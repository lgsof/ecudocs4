import json

from django.shortcuts import render, redirect
from django.views import View
from django.views import generic

from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.conf import settings

from django.contrib import messages

from app_cartaporte.models_doccpi import Cartaporte 
from app_manifiesto.models_docmci import Manifiesto, ManifiestoForm
from app_declaracion.models_docdti import Declaracion, DeclaracionForm
from app_entidades.models_Entidades import Cliente, Conductor, Vehiculo

def index (request):
	print ("\n\n\n+++  DEBUG: GET index")
	"""
	Función vista para la página inicio del sitio.
	"""
	# Genera contadores de algunos de los objetos principales
	num_clientes = Cliente.objects.all().count()
	num_conductors = Conductor.objects.all().count()
	num_vehiculos = Vehiculo.objects.all().count()
	num_cartaportes = Cartaporte.objects.all().count()
	num_manifestos = Manifiesto.objects.all().count()
	release        = getRelease ()

	# Number of visits to this view, as counted in the session variable.
	num_visits = request.session.get('num_visits', 0)
	request.session['num_visits'] = num_visits + 1

	# Renderiza la plantilla HTML index.html con los datos en la variable contexto
	return render( request, 'index.html',
		context={
				'release': release,
		         'num_clientes':num_clientes,
				 'num_conductors':num_conductors,
				 'num_vehiculos':num_vehiculos,
				 'num_cartaportes':num_cartaportes, 
				 'num_manifiestos':num_manifestos,
				 'num_visits': num_visits
				 })

def getRelease ():
	infoFile = settings.STATIC_ROOT + "/app_docs/json/ecuapassdocs-info.json"
	with open (infoFile) as fp:
		info = json.load (fp)
	return info ["release"]
	

# Decorador personalizado para requerir autenticación en una vista basada en clase
def login_required_class(view_func):
	return method_decorator(login_required, name='dispatch')(view_func)

#--------------------------------------------------------------------
#-- Cliente
#--------------------------------------------------------------------
class ClienteListView(generic.ListView):
	model = Cliente

class ClienteDetailView(generic.DetailView):
	model = Cliente
	
class ClienteCreate(login_required_class(CreateView)):
	model = Cliente
	fields = '__all__'


class ClienteUpdate(login_required_class(UpdateView)):
	model         = Cliente
	#template_name = "app_docs/cliente_form.html"
	fields = ['tipoId', 'numeroId', 'nombre','direccion','ciudad', 'pais']


class ClienteDelete(login_required_class(DeleteView)):
	model = Cliente
	success_url = reverse_lazy('clientes')


#--------------------------------------------------------------------
#-- Vehiculo
#--------------------------------------------------------------------
class VehiculoListView(generic.ListView):
	model = Vehiculo

class VehiculoDetailView(generic.DetailView):
	model = Vehiculo

#class ManifiestoListView(generic.ListView):
#	model = Manifiesto
#
#class ManifiestoDetailView (generic.DetailView):
#	model = Manifiesto

#--------------------------------------------------------------------
#-- Vehiculo
#--------------------------------------------------------------------
class VehiculoCreate(login_required_class(CreateView)):
	model = Vehiculo
	fields = '__all__'

class VehiculoUpdate(login_required_class(UpdateView)):
	model = Vehiculo
	fields = ['pais','marca','chasis','anho']

class VehiculoDelete(login_required_class(DeleteView)):
	model = Vehiculo
	success_url = reverse_lazy('vehiculos')

	#-- Overrided for deleting "remolque"
	def delete(self, request, *args, **kwargs):
		self.object = self.get_object()
		# Check if the truck has a trailer and delete it
		if self.object.remolque:
			self.object.remolque.delete()
		# Proceed with deleting the main truck
		return super().delete(request, *args, **kwargs)

	#-- Overrided for calling custom delete
	def post(self, request, *args, **kwargs):
		return self.delete (request, *args, **kwargs)

#--------------------------------------------------------------------
#-- Conductor
##--------------------------------------------------------------------
class ConductorListView(generic.ListView):
	model = Conductor

class ConductorDetailView(generic.DetailView):
	model = Conductor

class ConductorCreate(login_required_class(CreateView)):
	model = Conductor
	fields = '__all__'

class ConductorUpdate(login_required_class(UpdateView)):
	model = Conductor
	#template_name = "app_docs/conductor_form.html"
	fields = ['nombre','pais','licencia','fecha_nacimiento']

class ConductorDelete(login_required_class(DeleteView)):
	model = Conductor
	success_url = reverse_lazy('conductores')

#--------------------------------------------------------------------
#-- Manifiesto
#--------------------------------------------------------------------
#class ManifiestoCreate(login_required_class(CreateView)):
#	model = Manifiesto
#	fields = '__all__'
#
#class ManifiestoUpdate(login_required_class(UpdateView)):
#	model = Manifiesto
#	fields = ['vehiculo', 'cartaporte']
#
#class ManifiestoDelete (login_required_class(DeleteView)):
#	model = Manifiesto
#	success_url = reverse_lazy('manifiestos')

class InfoView(View):
	template_name = 'info_view.html'

	def get(self, request, *args, **kwargs):
		return render(request, self.template_name)

#--------------------------------------------------------------------
# Check if document exists. Base class for sublclases
#--------------------------------------------------------------------
class EcuapassDocDetailView (generic.DetailView):
	# GET request from listing 
	def get (self, request, *args, **kwargs):
		try:
			self.object = self.get_object()
			context = self.get_context_data(object=self.object)
			return self.render_to_response (context)
		except: 
			messages.add_message (request, messages.ERROR, "El documento no existe!")
			return render (request, 'messages.html')

	# POST request from form document
	def post (self, request, *args, **kwargs):
		try:
			self.object = self.get_object ()
			context = self.get_context_data (object=self.object)
			return self.render_to_response(context)
		except: 
			messages.add_message (request, messages.ERROR, "El documento no existe!")
			return render (request, 'messages.html')

#--------------------------------------------------------------------
# Messages view
#--------------------------------------------------------------------
def messagesView (request):
	if request.method == 'POST':
		# Process your form data... (replace with your actual logic)
		if form.is_valid():
			# Success message
			message = constants.SUCCESS
			get_messages(request).add(message, "Your form has been submitted successfully!")
		else:
			# Error message
			message = constants.ERROR
			get_messages(request).add(message, "There were errors in your form data. Please try again.")
	# Render your template
	return render(request, 'my_template.html')
