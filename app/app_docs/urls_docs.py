from django.urls import path

from app_manifiesto.views_ManifiestoDocView import *
from app_cartaporte.views_CartaporteDocView import *
from app_declaracion.views_DeclaracionDocView import *

from .views_Autocomplete import *
from . import views_docs
from .views_docs import InfoView, MessageView

urlpatterns = [
	#-- Other URLs  --------------------------------------------------
    path('info/', InfoView.as_view(), name='info_view'),
    path('message/', MessageView.as_view(), name='message-view'),
]

