
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django import forms
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, render
from django.http import Http404

from app_cartaporte.models_doccpi import Cartaporte
from app_docs.views_docs import EcuapassDocDetailView

#--------------------------------------------------------------------
#--------------------------------------------------------------------
# Decorador personalizado para requerir autenticación en una vista basada en clase
def login_required_class (view_func):
	return method_decorator (login_required, name='dispatch') (view_func)

#--------------------------------------------------------------------
#-- Cartaporte
#--------------------------------------------------------------------

class CartaporteListView (generic.ListView):
	model = Cartaporte

#-- Check id document exists
class CartaporteDetailView (EcuapassDocDetailView):
	model = Cartaporte

class CartaporteCreate (login_required_class (CreateView)):
	model = Cartaporte
	fields = '__all__'

class CartaporteUpdate (login_required_class (UpdateView)):
	model = Cartaporte
	fields = '__all__'
	#fields = ['tipo','remitente','destinatario','fecha_emision']

class CartaporteDelete (login_required_class (DeleteView)):
	model = Cartaporte
	success_url = reverse_lazy ('cartaporte-listado')

	def delete (self, request, *args, **kwargs):
		try:
			self.object = self.get_object ()
		except:
			messages.error (request, "Este documento ya no existe")
			raise Http404("This item no longer exists.")
			#return redirect (success_url)

		print ("-- On delete...")
		# Delete related objects
		related_objects = self.object.related_objects.all ()
		for obj in related_objects:
			print ("--obj:", obj)

		related_objects.delete ()

		# Delete the object using the default behavior
		return super ().delete (request, *args, **kwargs)


