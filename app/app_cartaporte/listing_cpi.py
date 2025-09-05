# For models
from app_docs.forms_docs import BuscarDocForm
from app_docs.listing_doc import DocumentosListadoView, DocumentosListadoTable

from django.utils.text import Truncator
import django_tables2 as tables

from .models_doccpi import Cartaporte

#----------------------------------------------------------
#-- View
#----------------------------------------------------------
class CartaportesListadoView (DocumentosListadoView):
    def __init__ (self):
        super().__init__ ("Cartaportes", Cartaporte, BuscarDocForm, CartaportesListadoTable)

#----------------------------------------------------------
# Table
#----------------------------------------------------------
class CartaportesListadoTable (DocumentosListadoTable):
	class Meta (DocumentosListadoTable.Meta):
		model         = Cartaporte
		urlDoc        = "cartaporte"
		fields        = ("row_number", "numero", "descripcion", "referencia", "remitente", "fecha_emision", "acciones")
		template_name = DocumentosListadoTable.template

	remitente = tables.Column(
		verbose_name="Remitente",
		attrs={"td": {"class": "text-truncate", "style": "max-width: 500px;"}}
	)

	def render_descripcion(self, value):
		return Truncator(value or "").chars(50)   # e.g. ~150 chars


