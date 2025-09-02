# For views
from django.views import View
from django.shortcuts import render

# For models
from app_docs.listing_doc import DocumentosListadoView, DocumentosListadoTable
from app_docs.forms_docs import BuscarDocForm
from .models_docmci import Manifiesto

#----------------------------------------------------------
#-- View
#----------------------------------------------------------
class ManifiestosListadoView (DocumentosListadoView):
    def __init__ (self):
        super().__init__ ("Manifiestos", Manifiesto, BuscarDocForm, ManifiestosListadoTable)

#----------------------------------------------------------
# Table
#----------------------------------------------------------
class ManifiestosListadoTable (DocumentosListadoTable):
	class Meta:
		model         = Manifiesto
		urlDoc        = "manifiesto"
		fields        = ("row_number", "numero", "fecha_emision", "vehiculo", "referencia", "acciones")
		template_name = DocumentosListadoTable.template
		attrs         = {'class': 'table table-striped table-bordered'}		



