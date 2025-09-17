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
	class Meta (DocumentosListadoTable.Meta):
		model         = Manifiesto
		urlDoc        = "manifiesto"
		fields        = ("row_number", "numero", "descripcion", "referencia", "vehiculo", "fecha_emision", "acciones")
		template_name = DocumentosListadoTable.template





