
from django.views import View, generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from django.http import JsonResponse
from django.urls import reverse_lazy

from app_manifiesto.models_docmci import Manifiesto
from app_docs.views_docs import EcuapassDocDetailView

#--------------------------------------------------------------------
#--------------------------------------------------------------------
# Decorador personalizado para requerir autenticación en una vista basada en clase
def login_required_class (view_func):
	return method_decorator (login_required, name='dispatch') (view_func)

#--------------------------------------------------------------------
#-- Manifiesto
#--------------------------------------------------------------------

class ManifiestoListView (generic.ListView):
	model = Manifiesto

class ManifiestoDetailView (EcuapassDocDetailView):
	model = Manifiesto

class ManifiestoCreate (login_required_class (CreateView)):
	model = Manifiesto
	fields = '__all__'

class ManifiestoUpdate (login_required_class (UpdateView)):
	model = Manifiesto
	fields = ['vehiculo', 'cartaporte']

class ManifiestoDelete (login_required_class (DeleteView)):
	model = Manifiesto
	success_url = reverse_lazy ('manifiesto-listado')

#--------------------------------------------------------------------
# Update manifiesto with cartaporte number from form
#--------------------------------------------------------------------
class UpdateCartaporteView (View):
	@method_decorator(csrf_protect)
	def post (self, request, *args, **kwargs):
		cartaporteNumber = request.POST.get ("cartaporteNumber")
		if cartaporteNumber:
			print ("+++ Updating 'manifiesto' table with CPIC: ", cartaporteNumber)
			return JsonResponse ({'status': 'success'})

		return JsonResponse ({'status': 'error'})

	#-- Not used as manifiesto saves all data, including cartaporte
	def updateCartaporte (self):
		if Cartaporte.objects.filter (numero=cartaporteNumber).exists():
			cartaporte = Cartaporte.objects.get (numero=cartaporteNumber)
			manifiesto = Manifiesto.objects.get (id=manifiestoId)
			manifiesto.cartaporte = cartaporte
			manifiesto.save()
		else:
			# Handle the case where the category doesn't exist
			print(f"Cartaporte  '{cartaporteNumber}' no existe.")


#----------------------------------------------------------
# List manifiestos using filters and table
#----------------------------------------------------------
def cartaporteListadoView (request):
	print ("+++ cartaporteListadoView : Pais: ", request.session.get ("pais"))
	pais        = request.session.get ("pais")
	cartaportes = Cartaporte.objects.filter (pais=pais)
	form        = CartaporteListadoForm (request.GET)
	table       = None

	if form.is_valid():
		print ("+++ DEBUG: form is valid")
		numero		  = form.cleaned_data.get('numero')
		fecha_emision = form.cleaned_data.get('fecha_emision')
		remitente     = form.cleaned_data.get('remitente')
		destinatario  = form.cleaned_data.get('destinatario')
		
		if numero:
			cartaportes = cartaportes.filter (numero__icontains=numero)
		if fecha_emision:
			cartaportes = cartaportes.filter (fecha_emision=fecha_emision)
		else:
			current_datetime = timezone.now()
			cartaportes = cartaportes.filter (fecha_emision__lte=current_datetime).order_by ('-fecha_emision')
		if remitente:
			cartaportes = cartaportes.filter (documento__txt02=remitente) # Remitente

		table = CartaportesTable (cartaportes)
	else:
		return ("+++ DEBUG: form is invalid")

	return render(request, 'documento_listado.html',
			   {'tipo': "Cartaportes", 'cartaportes': cartaportes, 'form': form, 'table': table})

