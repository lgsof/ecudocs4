"""
Base classes (View, Table) for listing ECUAPASS documents (Cartaporte, Manifiesto, Declaracion)

"""

# For views
from django.views import View
from django.shortcuts import render

# For forms
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field

# For tables
import django_tables2 as tables
from django_tables2 import RequestConfig
from django_tables2.utils import A

# For models
from app_docs.forms_docs import BuscarForma
from app_docs.listing_doc import BaseListadoTable

import django_tables2 as tables
from .models_Entidades import Vehiculo, Conductor, Cliente

#----------------------------------------------------------
#-- View
#----------------------------------------------------------
class EntidadesListadoView (View):
	def __init__ (self, docsTipo, DOCMODEL, DOCFORM, DOCTABLE):
		self.pais	   = None
		self.usuario   = None
		self.docsTipo  = docsTipo
		self.DOCMODEL  = DOCMODEL
		self.DOCFORM   = DOCFORM 
		self.DOCTABLE  = DOCTABLE

	# General and date search
	def get (self, request):
		# Firs, get all instances
		firstField = self.DOCMODEL._meta.fields [1].name
		instances  = self.DOCMODEL.objects.order_by (f"-{firstField}")

		form       = self.DOCFORM (request.GET)
		if not form.is_valid():
			return ("Forma inválida")

		searchPattern      = form.cleaned_data.get ('buscar')

		if searchPattern:
			object    = self.DOCMODEL()
			instances = object.searchModelAllFields (searchPattern)

		table = self.DOCTABLE (instances)
		RequestConfig (request, paginate={'per_page': 15}).configure (table) # Pagination

		args =	{'itemsTipo':self.docsTipo, 'itemsLista': instances, 
				 'itemsForma': form, 'itemsTable': table}
		return render(request, 'listing_entities.html', args)

##----------------------------------------------------------
## Base table used for listing Ecuapass docs 
##----------------------------------------------------------
class EntitiesListadoTable (BaseListadoTable):
	class Meta:
		abstract      = True
		template_name = "django_tables2/bootstrap4.html"
		attrs         = {'class': 'table table-striped table-bordered'}		

	#-- Define links for document table columns: numero, acciones (actualizar, eliminar)
	def __init__ (self, urlDoc, *args, **kwargs):
		self.urlEditar            = f"{urlDoc}-detail"
		self.urlEliminar          = f"{urlDoc}-eliminar"

		# Column for apply actions in the current item document
		self.base_columns ['acciones'] = tables.TemplateColumn(
			template_code='''
			<a href="{{ record.get_link_editar }}">{{ 'Editar' }}</a>,
			<a href="{{ record.get_link_eliminar }}">{{ 'Eliminar' }}</a>
			''',
			verbose_name='Acciones'
		)
		super().__init__ (*args, **kwargs)

#----------------------------------------------------------
#-- Vehiculos listing
#----------------------------------------------------------
class VehiculosListadoView (EntidadesListadoView):
	def __init__(self):
		super().__init__ ("vehiculos", Vehiculo, BuscarForma, VehiculosListadoTable)

class VehiculosListadoTable (EntitiesListadoTable):
	class Meta  (EntitiesListadoTable.Meta):
		model         = Vehiculo
		fields        = ("row_number", "placa", "tipo", "pais", "conductor", "acciones")

	def __init__ (self, *args, **kwargs):
		super().__init__ ("vehiculo", *args, **kwargs)
		self.urlEditarConductor = "conductor-editar"
		self.base_columns ['placa']      = tables.LinkColumn (self.urlEditar, args=[A('pk')])
		self.base_columns ['conductor']  = tables.LinkColumn (self.urlEditarConductor, args=[A('conductor__id')])
		super().__init__ ("vehiculo", *args, **kwargs) # To redraw the table

#----------------------------------------------------------
#-- Conductores listing
#----------------------------------------------------------
class ConductoresListadoView (EntidadesListadoView):
	def __init__(self):
		super().__init__ ("conductores", Conductor, BuscarForma, ConductoresListadoTable)

class ConductoresListadoTable (EntitiesListadoTable):
	class Meta (EntitiesListadoTable.Meta):
		model         = Conductor
		fields        = ("row_number", "documento", "nombre", "pais", "acciones")

	def __init__ (self, *args, **kwargs):
		super().__init__ ("conductor", *args, **kwargs)
		self.urlEditarConductor = "conductor-editar"
		self.base_columns ['documento']  = tables.LinkColumn (self.urlEditar, args=[A('pk')])
		super().__init__ ("conductor", *args, **kwargs)   # To redraw the table

#----------------------------------------------------------
#-- Clientes listing
#----------------------------------------------------------
class ClientesListadoView (EntidadesListadoView):
	def __init__(self):
		super().__init__ ("clientes", Cliente, BuscarForma, ClientesListadoTable)

class ClientesListadoTable (EntitiesListadoTable):
	class Meta (EntitiesListadoTable.Meta):
		model         = Cliente
		fields        = ("row_number", "numeroId","nombre","ciudad","direccion","acciones")

	def __init__ (self, *args, **kwargs):
		super().__init__ ("cliente", *args, **kwargs)
		self.urlEditarCliente = "cliente-editar"
		self.base_columns ['numeroId']  = tables.LinkColumn (self.urlEditar, args=[A('pk')])
		super().__init__ ("cliente", *args, **kwargs) # To redraw the table

	#-- Shows CIUDAD (PAIS)
	def render_ciudad (self, value, record):
		paisCode = record.pais [:2].upper()
		return value + f" ({paisCode})"
					 
