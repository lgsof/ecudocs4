from django.db import models

from ecuapassdocs.info.ecuapass_utils import Utils

import app_manifiesto as appMci
from app_docs.models_docbase import DocBaseModel
from ecuapassdocs.utils.models_scripts import Scripts
from app_entidades.models_Entidades import Cliente

#--------------------------------------------------------------------
# Cartaporte Model
#--------------------------------------------------------------------
class Cartaporte (DocBaseModel):
	class Meta:
		db_table = "cartaporte"
		constraints = [
			# numero debe ser único por empresa (ajusta si no aplica)
			models.UniqueConstraint (fields=["empresa", "numero"], name="uniq_cartaporte_empresa_numero"),
		]		

	remitente    = models.ForeignKey (Cliente, related_name="cartaportes_remitente", on_delete=models.SET_NULL, null=True, blank=True)
	destinatario = models.ForeignKey (Cliente, related_name="cartaportes_destinatario", on_delete=models.SET_NULL, null=True, blank=True)

	#-- Get str for printing -----------------------------------------
	def __str__ (self):
		remitente = self.txtFields.get ("txt02") or self.remitente or "-"
		return f"{self.numero}, {remitente}"

	#-- Save doc to DB -------------------------------------------------
	def update (self, doc):
		print (f"\n+++ Guardando cartaporte número: '{doc.numero}'")
		if doc.numero:
			# Set common fields
			super().update (doc)
			# Set specific fields
			self.remitente    = self.getTxtRemitente ()  
			# Save and create HttpResponse
			return super().saveCreateResponse ()

	#---------------------------------------------------------------
	# Get/Set txt fields
	#---------------------------------------------------------------
	def getTxtRemitente (self):
		text    = self.getTxt ("txt02")
		cliente = Scripts.getSaveClienteInstanceFromText (text, type="02_Remitente") if text else None
		return cliente 

	def getTxtDestinatario (self):
		cliente = Scripts.getSaveClienteInstanceFromText (self.getTxt ("txt03"), type="03_Destinatario")
		return cliente

	def getMercanciaInfo(self):
		return {
			"cantidad":   self.txtFields.get("txt10"),
			"marcas":	  self.txtFields.get("txt11"),
			"descripcion": self.txtFields.get("txt12"),
		}	

	#-- Check if the CPI has a "manifiesto" -------------------------
	def hasManifiesto (self):
		cartaporteNumber = self.numero
		try:
			manifiesto = appMci.models_docmci.Manifiesto.objects.get (cartaporte=self.id)
			return True
		except appMci.models_docmci.Manifiesto.DoesNotExist:
			print (f"+++ No existe manifiesto para cartaporte nro: '{cartaporteNumber}´")
			return False


