from django.urls import path

from app_docs.views_EcuapassDocView import docView
from app_cartaporte.views_CartaporteDocView import *
from app_cartaporte import views_cpi
from app_docs.views_Autocomplete import *

from .listing_cpi import CartaportesListadoView
from .views_CartaportePredictions import CartaportePredictionsView

urlpatterns = [
	#-- URLs cartaporte -----------------------------------------------
    path("", CartaporteDocView.as_view(), name="cartaporte"),
    path('listado/', CartaportesListadoView.as_view(), name='cartaporte-listado'),

	# Create/Edit
    path("nuevodoc/", docView, name="cartaporte-nuevodoc"),
    path("nuevo/", CartaporteDocView.as_view(), name="cartaporte-nuevo"),
	path('editardoc/<int:pk>', docView, name='cartaporte-editardoc'),
	path('editar/<int:pk>', CartaporteDocView.as_view(), name='cartaporte-editar'),

	# PDF, detail, remove
	path('pdf_original/<int:pk>', CartaporteDocView.as_view(), name='cartaporte-pdf_original'),
	path('pdf_copia/<int:pk>', CartaporteDocView.as_view(), name='cartaporte-pdf_copia'),
	path('pdf_paquete/<int:pk>', CartaporteDocView.as_view(), name='cartaporte-pdf_paquete'),
	path('clonar/<int:pk>', CartaporteDocView.as_view(), name='cartaporte-clonar'),
    path('detalle/<pk>', views_cpi.CartaporteDetailView.as_view(), name='cartaporte-detalle'),
	path('borrar/<int:pk>', views_cpi.CartaporteDelete.as_view(), name='cartaporte-delete'),

	# Input fields prediction
    path('prediccion/<txtId>', CartaportePredictionsView.as_view(), name='cartaporte-prediccion'),
]

