from django.urls import path

from app_manifiesto.views_ManifiestoDocView import *
from app_cartaporte.views_CartaporteDocView import *
from app_declaracion.views_DeclaracionDocView import *

from .listing_entities import VehiculosListadoView
from .listing_entities import ConductoresListadoView
from .listing_entities import ClientesListadoView

from .views_Autocomplete import *
from . import views_docs
from .views_docs import InfoView

urlpatterns = [
    #path('', views_docs.index, name='index'),
    #path ('', views_docs.principal, name='principal'),
    #path ('index', views_docs.index, name='index'),

	#-- URLs entities --------------------------------------------------
    #path('clientes/', views_docs.ClienteListView.as_view(), name='clientes'),
    path('clientes/', ClientesListadoView.as_view(), name='clientes'),
    path('cliente/<pk>', views_docs.ClienteDetailView.as_view(), name='cliente-detail'),
    path('cliente/create/', views_docs.ClienteCreate.as_view(), name='cliente-create'),
    path('cliente/editar/<pk>', views_docs.ClienteUpdate.as_view(), name='cliente-editar'),
    path('cliente/eliminar/<pk>', views_docs.ClienteDelete.as_view(), name='cliente-eliminar'),

    #path('vehiculos/', views_docs.VehiculoListView.as_view(), name='vehiculos'),
    path('vehiculos/', VehiculosListadoView.as_view(), name='vehiculos'),
    path('vehiculo/<pk>', views_docs.VehiculoDetailView.as_view(), name='vehiculo-detail'),
    path('vehiculo/create/', views_docs.VehiculoCreate.as_view(), name='vehiculo-create'),

    path('vehiculo/editar/<pk>', views_docs.VehiculoUpdate.as_view(), name='vehiculo-editar'),
    path('vehiculo/eliminar/<pk>', views_docs.VehiculoDelete.as_view(), name='vehiculo-eliminar'),

    path('conductores/', ConductoresListadoView.as_view(), name='conductores'),
    path('conductor/<pk>', views_docs.ConductorDetailView.as_view(), name='conductor-detail'),
    path('conductor/create/', views_docs.ConductorCreate.as_view(), name='conductor-create'),
    path('conductor/editar/<pk>', views_docs.ConductorUpdate.as_view(), name='conductor-editar'),
    path('conductor/eliminar/<pk>', views_docs.ConductorDelete.as_view(), name='conductor-eliminar'),

	#-- URLs options -----------------------------------------------------
    #path('opciones-cliente/', ClienteOptionsView.as_view(), name='opciones-cliente'),

	#-- Other URLs  --------------------------------------------------
    path('info/', InfoView.as_view(), name='info_view'),
]

