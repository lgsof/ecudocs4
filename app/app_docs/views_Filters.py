from django.shortcuts import render
from django import forms
from django.utils import timezone

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

from .models_docs import Cartaporte, Manifiesto, Declaracion
from app_docs.models_Entidades import Cliente
#from .forms import CartaportesFilterForm, ManifiestosFilterForm

#--------------------------------------------------------------------
#-- CartaportesFilter Form
#--------------------------------------------------------------------
class CartaportesFilterForm (forms.Form):
	numero		   = forms.CharField(required=False)
	fecha_emision  = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
	remitente	   = forms.CharField(required=False)
	#remitente      = forms.ModelChoiceField (queryset=Cliente.objects.all(), required=False)

	def __init__(self, *args, **kwargs):
		super (CartaportesFilterForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'GET'
		self.helper.layout = Layout(
			Row (
				Column ('numero', css_class='col'),
				Column ('fecha_emision', css_class='col'),
				Column ('remitente', css_class='col'),
				css_class='row'
			),
			Submit ('submit', 'Filtrar', css_class='btn btn-primary')
		)

#--------------------------------------------------------------------
#-- CartaportesFilter View
#--------------------------------------------------------------------
def cartaportesFilterView (request):
	print ("+++ cartaportesFilterView : Pais: ", request.session.get ("pais"))
	pais = request.session.get ("pais")
	cartaportes = Cartaporte.objects.filter (pais=pais)
	form  = CartaportesFilterForm (request.GET)
	if form.is_valid():
		numero		  = form.cleaned_data.get('numero')
		fecha_emision = form.cleaned_data.get('fecha_emision')
		remitente	  = form.cleaned_data.get('remitente')

		if numero:
			cartaportes = cartaportes.filter (numero__icontains=numero)
		if fecha_emision:
			cartaportes = cartaportes.filter (fecha_emision=fecha_emision)
		else:
			current_datetime = timezone.now()
			cartaportes = cartaportes.filter (fecha_emision__lte=current_datetime).order_by ('-fecha_emision')

		if remitente:
			cartaportes = cartaportes.filter (documento__txt02=remitente) # Remitente

	return render(request, 'app_cartaporte/cartaporte_listado.html', {'cartaporte_list': cartaportes, 'form': form})

#--------------------------------------------------------------------
#-- ManifiestosFilter Form
#--------------------------------------------------------------------
class ManifiestosFilterForm (forms.Form):
	numero		   = forms.CharField(required=False)
	fecha_emision  = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
	conductor	   = forms.CharField(required=False)

	def __init__(self, *args, **kwargs):
		super (ManifiestosFilterForm, self).__init__(*args, **kwargs)

		self.helper = FormHelper()
		self.helper.layout = Layout(
			Row (
				Column ('numero', css_class='col'),
				Column ('fecha_emision', css_class='col'),
				Column ('conductor', css_class='col'),
				css_class='row'
			),
			Submit ('submit', 'Filtrar', css_class='btn btn-primary')
		)

#--------------------------------------------------------------------
#-- ManifiestosFilter View
#--------------------------------------------------------------------
def manifiestosFilterView (request):
	manifiestos = Manifiesto.objects.all()
	form  = ManifiestosFilterForm (request.GET)
	if form.is_valid():
		numero		  = form.cleaned_data.get('numero')
		fecha_emision = form.cleaned_data.get('fecha_emision')
		conductor	  = form.cleaned_data.get('conductor')

		if numero:
			manifiestos = manifiestos.filter (numero__icontains=numero)
		if fecha_emision:
			manifiestos = manifiestos.filter (fecha_emision=fecha_emision)
		if conductor:
			manifiestos = manifiestos.filter (documento__txt13=conductor) # Conductor

	return render(request, 'app_manifiesto/manifiesto_listado.html', {'manifiesto_list': manifiestos, 'form': form})

#--------------------------------------------------------------------
#-- DeclaracionesFilter Form
#--------------------------------------------------------------------
class DeclaracionesFilterForm (forms.Form):
	numero		   = forms.CharField(required=False)
	fecha_emision  = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
	conductor	   = forms.CharField(required=False)

	def __init__(self, *args, **kwargs):
		super (DeclaracionesFilterForm, self).__init__(*args, **kwargs)

		self.helper = FormHelper()
		self.helper.layout = Layout(
			Row (
				Column ('numero', css_class='col'),
				Column ('fecha_emision', css_class='col'),
				Column ('conductor', css_class='col'),
				css_class='row'
			),
			Submit ('submit', 'Filtrar', css_class='btn btn-primary')
		)

#--------------------------------------------------------------------
#-- DeclaracionesFilter View
#--------------------------------------------------------------------
def declaracionesFilterView (request):
	declaraciones = Declaracion.objects.all()
	form  = DeclaracionesFilterForm (request.GET)
	if form.is_valid():
		numero		  = form.cleaned_data.get('numero')
		fecha_emision = form.cleaned_data.get('fecha_emision')
		conductor	  = form.cleaned_data.get('conductor')

		if numero:
			declaraciones = declaraciones.filter (numero__icontains=numero)
		if fecha_emision:
			declaraciones = declaraciones.filter (fecha_emision=fecha_emision)
		if conductor:
			declaraciones = declaraciones.filter (documento__txt13=conductor) # Conductor

	return render(request, 'app_declaracion/declaracion_listado.html', {'declaracion_list': declaraciones, 'form': form})

