from django.urls import path,include

from . import views

urlpatterns = [
    path('', views.InfoView.as_view(), name='reportes'),
]
