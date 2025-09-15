# app_usuarios/urls_onboarding.py
from django.urls import path
from .views_onboarding import crear_empresa, onboarding_exito

urlpatterns = [
    path ("onboarding/empresas/nueva/", crear_empresa, name="onboarding_crear_empresa"),
    path ("onboarding/empresas/exito/", onboarding_exito, name="onboarding_exito"),
]

