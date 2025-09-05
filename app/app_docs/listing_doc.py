"""
Base classes (View, Table) for listing ECUAPASS documents (Cartaporte, Manifiesto, Declaracion)
"""

# For views
from django.views import View
from django.shortcuts import render

# For forms
from django import forms
from django.utils import timezone, formats
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field

# For tables
from datetime import datetime
from datetime import date

import django_tables2 as tables
from django_tables2 import RequestConfig

from django.urls import reverse
from django.utils.html import format_html
from django_tables2.utils import A

from .models_docbase import DocBaseModel
from ecuapassdocs.utils.models_scripts import Scripts

#----------------------------------------------------------
#-- View
#----------------------------------------------------------
class DocumentosListadoView (View):
	def __init__ (self, docsTipo, DOCMODEL, DOCFORM, DOCTABLE):
		self.pais	   = None
		self.usuario   = None
		self.docsTipo  = docsTipo
		self.DOCMODEL  = DOCMODEL
		self.DOCFORM   = DOCFORM 
		self.DOCTABLE  = DOCTABLE

	# General and date search
	def get (self, request):
		print (f"\n+++ In lising_doc::get...'")
		# Firs, get all instances
		#numero       = self.DOCMODEL._meta.fields [1].name
		#fecha_emision = self.DOCMODEL._meta.fields [2].name
		#instances  = self.DOCMODEL.objects.order_by ("-fecha_emision", "-numero")
		instances  = self.DOCMODEL.objects.order_by ("-numero")

		form       = self.DOCFORM (request.GET)
		if not form.is_valid():
			return ("Forma inválida")

		searchPattern      = form.cleaned_data.get ('buscar')
		searchFechaEmision = form.cleaned_data.get ('fecha_emision')

		if searchPattern:
			object    = self.DOCMODEL()
			instances = object.searchModelAllFields (searchPattern)

		if searchFechaEmision:
			object    = self.DOCMODEL()
			instances = instances.filter (fecha_emision=searchFechaEmision)  # Assuming 'created_at' is the date field

		table = self.DOCTABLE (instances)
		RequestConfig (request, paginate={'per_page': 15}).configure (table) # Pagination

		args =	{'itemsTipo':self.docsTipo, 'itemsLista': instances, 
				 'itemsForma': form, 'itemsTable': table}
		return render(request, 'listing_entities.html', args)

#----------------------------------------------------------
#-- Forma
#----------------------------------------------------------
class BuscarDocForm (forms.Form):
	buscar = forms.CharField(required=False,label="")
	fecha_emision  = forms.DateField(required=False, label=False,
								  widget=forms.DateInput (attrs={'type':'date'}))

	def __init__(self, *args, **kwargs):
		super ().__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'GET'
		self.helper.layout = Layout(
			Row (
				Column(Field('buscar', placeholder="Digite texto a buscar...", label=False), css_class='search_field'),
				Column (Field ('fecha_emision', placeholder="Seleccione fecha a buscar...", label=False), css_class='search_field'),
				Column (Submit ('submit', 'Buscar'), css_class='search_button'),
				css_class='form-row'
			)
			#Submit ('submit', 'Filtrar', css_class='btn btn-primary')
		)

#----------------------------------------------------------
# Base table used for listing docs and entities
# 
#----------------------------------------------------------
class BaseListadoTable (tables.Table):
	row_number = tables.Column (empty_values=(), verbose_name="No.")  # Add a custom column for enumeration
	class Meta:
		abstract = True

	def __init__ (self, *args, **kwargs):
		super ().__init__ (*args, **kwargs)
		self.counter = 0  # Initialize a counter to keep track of rows

	#-- This method returns the row number for each row in the table.
	def render_row_number(self):
		self.counter += 1
		return self.counter

#----------------------------------------------------------
# Base table used for listing the three doc types: CPI, MCI, DTI
#----------------------------------------------------------
class DocumentosListadoTable (BaseListadoTable):
	template = "django_tables2/bootstrap4.html"

	class Meta:
		abstract = True
		attrs = {
			"class": "table table-striped table-bordered small-table",
			"style": "font-size:14px; line-height:1.0;"  # test
		}	

	descripcion = tables.Column(
		verbose_name="Descripción",
		attrs={"td": {"class": "text-truncate", "style": "max-width:480px; white-space:normal; overflow:hidden;"}}
	)
	fecha_emision = tables.Column (
		verbose_name="F. Emisión"
	) 

	#-- Define links for document table columns: numero, acciones (actualizar, eliminar)
	def __init__ (self, *args, **kwargs):
		self.urlDoc               = getattr (self.Meta, 'urlDoc', 'default-url')
		self.urlEditar            = f"{self.urlDoc}-editardoc"

		self.base_columns ['numero']  = tables.LinkColumn (self.urlEditar, args=[A('pk')])
		# Column for apply actions in the current item document
		self.base_columns ['acciones'] = tables.TemplateColumn(
			template_code='''
			<a href="{{ record.get_link_editar }}" target='_blank'>Editar</a>
			<a href="{{ record.get_link_pdf }}" target='_blank'>PDF</a>
			<a href="{{ record.get_link_eliminar }}" target='_blank'>Eliminar</a>
			<a href="{{ record.get_link_detalle }}" target='_blank'>Detalle</a>
			''',
			verbose_name='Acciones'
		)
		super().__init__ (*args, **kwargs)
		#self.counter = 0  # Initialize a counter to keep track of rows

	#-- Generate a URL for each record
	def render_numero (self, value, record):
		return format_html('<a href="{}" target="_blank" >{}</a>', 
					 reverse(self.urlEditar, args=[record.pk]), value)

       # Use Django’s format system
	def render_fecha_emision(self, value):
		return formats.date_format(value, "SHORT_DATE_FORMAT")  
		# or value.strftime("%d/%m/%Y")

	def render_descripcion(self, value):
		return Truncator(value or "").chars(50)   # e.g. ~150 chars

		## Ensure value is a datetime object before formatting
		#if isinstance(value, (datetime, (date, datetime))):
		#	return value.strftime('%m/%d/%Y')  # Format to 'dd/mm/yyyy'
		#return ''


