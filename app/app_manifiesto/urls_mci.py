from django.urls import path

from app_docs.views_EcuapassDocView import docView
from app_manifiesto.views_ManifiestoDocView import *
from app_manifiesto import views_mci
from app_docs.views_Autocomplete import *

from .listing_mci import ManifiestosListadoView

urlpatterns = [
	#-- URLs manifiesto -----------------------------------------------
    path("", ManifiestoDocView.as_view(), name="manifiesto"),
    path('listado/', ManifiestosListadoView.as_view(), name='manifiesto-listado'),

	# Create/Edit
    path("nuevodoc/", docView, name="manifiesto-nuevodoc"),
    path("nuevo/", ManifiestoDocView.as_view(), name="manifiesto-nuevo"),
	path('editardoc/<int:pk>', docView, name='manifiesto-editardoc'),
	path('editar/<int:pk>', ManifiestoDocView.as_view(), name='manifiesto-editar'),

	# PDF, detail, remove
	path('pdf_original/<int:pk>', ManifiestoDocView.as_view(), name='manifiesto-pdf_original'),
	path('pdf_copia/<int:pk>', ManifiestoDocView.as_view(), name='manifiesto-pdf_copia'),
	path('pdf_paquete/<int:pk>', ManifiestoDocView.as_view(), name='manifiesto-pdf_paquete'),
	path('clonar/<int:pk>', ManifiestoDocView.as_view(), name='manifiesto-clonar'),
    path('detalle/<pk>', views_mci.ManifiestoDetailView.as_view(), name='manifiesto-detalle'),
	path('borrar/<int:pk>', views_mci.ManifiestoDelete.as_view(), name='manifiesto-delete'),

	# Update manifiesto with cartaporte and related info
	path('<pk>/actualizar-cartaporte/', views_mci.UpdateCartaporteView.as_view(), name='manifiesto-cartaporte')
]

