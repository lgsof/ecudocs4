# app_main/urls.py
from django.contrib import admin
from django.urls import path, include
from app_docs import views_docs
from app_docs.views_Autocomplete import (
    ClienteOptionsView, CiudadPaisOptionsView, CiudadPaisFechaOptionsView,
    VehiculoOptionsView, ConductorOptionsView, CartaporteOptionsView,
    PlacaOptionsView, ManifiestoOptionsView
)

admin.site.site_header = "Creación/Almacenamiento de Documentos del ECUAPASS"
admin.site.site_title  = "Creación/Almacenamiento de Documentos del ECUAPASS"
admin.site.index_title = "Creación/Almacenamiento de Documentos del ECUAPASS Admin"

urlpatterns = [
    path("admin/", admin.site.urls),  # admin primero

    # Home (/) al index
    path("", views_docs.index, name="index"),

    # Onboarding (si no usas subdominio o para crear empresas)
    path("", include("app_usuarios.urls_onboarding")),

    # Apps
    path("usuarios/",   include("app_usuarios.urls_user")),
    path("documentos/", include("app_docs.urls_docs")),
    path("cartaporte/", include("app_cartaporte.urls_cpi")),
    path("manifiesto/", include("app_manifiesto.urls_mci")),
    path("declaracion/",include("app_declaracion.urls_dti")),
    path("entidades/", include("app_entidades.urls_entidades")),
    path("reportes/",   include("appreportes.urls")),

    # Autocomplete
    path("opciones-cliente",      ClienteOptionsView.as_view(), name="opciones-cliente"),
    path("opciones-lugar",        CiudadPaisOptionsView.as_view(), name="opciones-lugar"),
    path("opciones-lugar-fecha",  CiudadPaisFechaOptionsView.as_view(), name="opciones-lugar-fecha"),
    path("opciones-vehiculo",     VehiculoOptionsView.as_view(), name="opciones-vehiculo"),
    path("opciones-conductor",    ConductorOptionsView.as_view(), name="opciones-conductor"),
    path("opciones-cartaporte",   CartaporteOptionsView.as_view(), name="opciones-cartaporte"),
    path("opciones-placa",        PlacaOptionsView.as_view(), name="opciones-placa"),
    path("opciones-manifiesto",   ManifiestoOptionsView.as_view(), name="opciones-manifiesto"),
]

