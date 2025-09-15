import os, tempfile, json
from datetime import date

from django.db import models
from django.urls import reverse  # To generate URLS by reversing URL patterns

from ecuapassdocs.info.ecuapass_utils import Utils

from app_docs.models_docbase import DocBaseModel

from app_cartaporte.models_doccpi import Cartaporte
from app_usuarios.models import Usuario
from ecuapassdocs.utils.models_scripts import Scripts

from app_entidades.models_Entidades import Cliente, Conductor, Vehiculo

#--------------------------------------------------------------------
# Model DeclaracionForm
#--------------------------------------------------------------------
class DeclaracionForm (models.Model):
	class Meta:
		db_table = "declaracionform"

	numero = models.CharField (max_length=20)
	txt0a = models.CharField (max_length=20, null=True)
	txt00 = models.CharField (max_length=20, null=True)
	txt01 = models.CharField (max_length=200, null=True)
	txt02 = models.CharField (max_length=200, null=True)
	txt03 = models.CharField (max_length=200, null=True)
	txt04 = models.CharField (max_length=200, null=True)
	txt05 = models.CharField (max_length=200, null=True)
	txt06 = models.CharField (max_length=200, null=True)
	txt07 = models.CharField (max_length=200, null=True)
	txt08 = models.CharField (max_length=200, null=True)
	txt09 = models.CharField (max_length=200, null=True)
	txt10 = models.CharField (max_length=200, null=True)
	txt11 = models.CharField (max_length=200, null=True)
	txt12 = models.CharField (max_length=200, null=True)
	txt13 = models.CharField (max_length=200, null=True)
	txt14 = models.CharField (max_length=200, null=True)
	#-- Informacion mercancia
	txt15 = models.CharField (max_length=200, null=True)    # Cartaporte
	txt16 = models.CharField (max_length=800, null=True)    # Descripción
	txt17 = models.CharField (max_length=200, null=True)    # Cantidad Bultos
	txt18 = models.CharField (max_length=200, null=True)    # Embalaje/Marcas
	txt19_1 = models.CharField (max_length=200, null=True)  # Peso bruto
	txt19_2 = models.CharField (max_length=200, null=True)  # Peso bruto total
	txt19_3 = models.CharField (max_length=200, null=True)  # Peso neto
	txt19_4 = models.CharField (max_length=200, null=True)  # Peso neto total
	txt20_1 = models.CharField (max_length=200, null=True)  # Otra medida
	txt20_2 = models.CharField (max_length=200, null=True)  # Otra medida total
	txt21 = models.CharField (max_length=200, null=True)    # INCOTERM
	txt22 = models.CharField (max_length=200, null=True)
	txt23 = models.CharField (max_length=200, null=True)
	txt24 = models.CharField (max_length=200, null=True)
	txt25 = models.CharField (max_length=200, null=True)
	txt26 = models.CharField (max_length=200, null=True)

	def __str__ (self):
		return f"{self.numero}, {self.txt03}"
	
#--------------------------------------------------------------------
# Model Declaracion
#--------------------------------------------------------------------
class Declaracion (DocBaseModel):
	class Meta:
		db_table = "declaracion"

	documento    = models.OneToOneField (DeclaracionForm,
									   on_delete=models.CASCADE, null=True)
	#declarante   = models.ForeignKey (Cliente, related_name="declaraciones_declarante",
	#                                   on_delete=models.SET_NULL, null=True)
	remitente    = models.ForeignKey (Cliente, related_name="declaraciones_remitente",
	                                   on_delete=models.SET_NULL, null=True)
	destinatario = models.ForeignKey (Cliente, related_name="declaraciones_destinatario",
	                                   on_delete=models.SET_NULL, null=True)

	cartaporte   = models.ForeignKey (Cartaporte, on_delete=models.SET_NULL, null=True)

	def get_absolute_url(self):
		"""Returns the url to access a particular language instance."""
		return reverse('declaracion-detail', args=[str(self.id)])

	def __str__ (self):
		return f"{self.numero}, {self.cartaporte}"

	def setValues (self, declaracionForm, docFields, pais, username):
		# Base values
		super().setValues (declaracionForm, docFields, pais, username)

		# Document values
		self.declarante    = Scripts.getSaveClienteInstance ("02_Declarante", docFields)
		self.remitente     = Scripts.getSaveClienteInstance ("03_Remitente", docFields)
		self.destinatario  = Scripts.getSaveClienteInstance ("04_Destinatario", docFields)
		self.fecha_emision = self.getDocFechaEmision (docFields)

		self.cartaporte    = Scripts.getCartaporteInstanceFromDocFields (docFields, "DECLARACION")

