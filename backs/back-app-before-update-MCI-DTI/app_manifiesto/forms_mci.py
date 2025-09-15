
from django.shortcuts import render

from django import forms
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

from .models_docmci import Manifiesto
from .tables_mci import ManifiestosTable

#--------------------------------------------------------------------
#-- CartaportesFilter Form
#--------------------------------------------------------------------
class ManifiestoListadoForm (forms.Form):
	numero		   = forms.CharField(required=False)
	fecha_emision  = forms.DateField(required=False,
								  widget=forms.DateInput (attrs={'type':'date'}))
	#remitente		= forms.ModelChoiceField (queryset=Cliente.objects.all(), required=False)

	def __init__(self, *args, **kwargs):
		super (ManifiestoListadoForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'GET'
		self.helper.layout = Layout(
			Row (
				Column ('numero', css_class='col'),
				Column ('fecha_emision', css_class='col'),
				css_class='row'
			),
			Submit ('submit', 'Filtrar', css_class='btn btn-primary')
		)

def manifiestoListadoView (request):
	print ("+++ manifiestoListadoForm : Pais: ", request.session.get ("pais"))
	pais		= request.session.get ("pais")
	manifiestos = Manifiesto.objects.filter (pais=pais)
	form		= ManifiestoListadoForm (request.GET)
	table		= None

	if form.is_valid():
		print ("+++ DEBUG: form is valid")
		numero		  = form.cleaned_data.get('numero')
		fecha_emision = form.cleaned_data.get('fecha_emision')
		
		if numero:
			manifiestos = manifiestos.filter (numero__icontains=numero)
		if fecha_emision:
			manifiestos = manifiestos.filter (fecha_emision=fecha_emision)
		else:
			current_datetime = timezone.now()
			manifiestos = manifiestos.filter (fecha_emision__lte=current_datetime).order_by ('-fecha_emision')

		table = ManifiestosTable (manifiestos)
	else:
		return ("+++ DEBUG: form is invalid")

	return render(request, 'documento_listado.html',
			   {'tipoDocs': "Manifiestos", 'listaDocs': manifiestos, 'formaDocs': form, 'tablaDocs': table})

