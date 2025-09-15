# For models
from app_docs.listing_doc import DocumentosListadoView, DocumentosListadoTable
from app_docs.forms_docs import BuscarDocForm
from .models_docdti import Declaracion

#----------------------------------------------------------
#-- View
#----------------------------------------------------------
class DeclaracionesListadoView (DocumentosListadoView):
    def __init__ (self):
        super().__init__ ("Declaraciones", Declaracion, BuscarDocForm, DeclaracionesListadoTable)

#----------------------------------------------------------
# Table
#----------------------------------------------------------
class DeclaracionesListadoTable (DocumentosListadoTable):
	class Meta:
		model         = Declaracion
		urlDoc        = "declaracion"
		fields        = ("row_number", "numero", "fecha_emision", "referencia", "acciones")
		template_name = DocumentosListadoTable.template
		attrs         = {'class': 'table table-striped table-bordered'}		

