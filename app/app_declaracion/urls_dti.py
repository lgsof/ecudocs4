from django.urls import path

from app_docs.views_EcuapassDocView import docView
from app_declaracion.views_DeclaracionDocView import *
from app_declaracion import views_dti
from app_docs.views_Autocomplete import *

from .listing_dti import DeclaracionesListadoView

urlpatterns = [
	#-- URLs declaracion -----------------------------------------------
    path("", DeclaracionDocView.as_view(), name="declaracion"),
    path('listado/', DeclaracionesListadoView.as_view(), name='declaracion-listado'),

	# Create/Edit
    path("nuevodoc/", docView, name="declaracion-nuevodoc"),
    path("nuevo/", DeclaracionDocView.as_view(), name="declaracion-nuevo"),
	path('editardoc/<int:pk>', docView, name='declaracion-editardoc'),
	path('editar/<int:pk>', DeclaracionDocView.as_view(), name='declaracion-editar'),

	# PDF, detail, remove
	path('pdf_original/<int:pk>', DeclaracionDocView.as_view(), name='declaracion-pdf_original'),
	path('pdf_copia/<int:pk>', DeclaracionDocView.as_view(), name='declaracion-pdf_copia'),
	path('pdf_paquete/<int:pk>', DeclaracionDocView.as_view(), name='declaracion-pdf_paquete'),
	path('clonar/<int:pk>', DeclaracionDocView.as_view(), name='declaracion-clonar'),
    path('detalle/<pk>', views_dti.DeclaracionDetailView.as_view(), name='declaracion-detalle'),
	path('borrar/<int:pk>', views_dti.DeclaracionDelete.as_view(), name='declaracion-delete')
]

