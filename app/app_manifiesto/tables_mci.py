# tables.py
from datetime import datetime
from datetime import date

import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html
from django_tables2.utils import A
from .models_docmci import Manifiesto

#----------------------------------------------------------
# Creates a table for Manifiesto results
#----------------------------------------------------------
class ManifiestosTable (tables.Table):
	class Meta:
		model = Manifiesto
		template_name = "django_tables2/bootstrap4.html"
		fields = ("numero", "fecha_emision")

	#-- Create a link on doc number
	def render_numero (self, value, record):
		# Generate a URL for each record
		return format_html('<a href="{}">{}</a>', reverse('manifiesto-editar', args=[record.pk]), value)

	#-- Change format to agree with form date format
	def render_fecha_emision(self, value):
		# Ensure value is a datetime object before formatting
		if isinstance(value, (datetime, (date, datetime))):
			return value.strftime('%m/%d/%Y')  # Format to 'dd/mm/yyyy'
		return ''

