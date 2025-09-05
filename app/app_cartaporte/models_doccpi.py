import re

from django.db import models

from ecuapassdocs.info.ecuapass_extractor import Extractor
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

	# ---------------- Helpers --------------------------------------
	#-- Get str for printing
	def __str__ (self):
		remitente = self.txtFields.get ("txt02") or self.remitente or "-"
		return f"{self.numero}, {remitente}"

	# ---------------------------------------------------------------
	# Save doc to DB
	# ---------------------------------------------------------------
	def update (self, doc):
		print (f"\n+++ Guardando cartaporte número: '{doc.numero}'")
		if doc.numero:
			self.numero        = doc.numero
			empresaInstance    = Scripts.getEmpresaByNickname (doc.empresa)
			self.empresa       = empresaInstance
			usuarioInstance    = Scripts.getUsuarioByUsernameEmpresa (doc.usuario, empresaInstance.id)
			self.usuario       = usuarioInstance
			self.pais          = doc.pais
			self.descripcion   = self.getTxtDescripcion ()
			self.fecha_emision = self.getTxtFechaEmision ()

			# Set txt fields
			self.setTxtFields (doc.getTxtFields ())
			self.setTxtNumero (self.numero)
			self.setTxtPais (self.pais)

			docFields         = doc.getDocFields ()
			self.remitente    = self.getTxtRemitente ()  
			print (f"\n+++ {self.txtFields=}'")

			self.save()

	#-- Return docParams from doc DB instance
	def getDocParams (self, inputParams):
		docParams = inputParams
		docParams ["id"]["value"]       = self.id
		docParams ["numero"]["value"]   = self.numero
		docParams ["pais"]["value"]     = self.pais
		docParams ["usuario"]["value"]  = self.usuario.username
		docParams ["empresa"]["value"]  = self.empresa.nickname

		txtFields = self.getTxtFields ()
		for k, v in txtFields.items():	# Not include "numero" and "id"
			text     = txtFields [k]
			maxChars = inputParams [k]["maxChars"]
			newText  = Utils.breakLongLinesFromText (text, maxChars)
			docParams [k]["value"] = newText if newText else ""
		return docParams


	#-- Check if the CPI has a "manifiesto"
	def hasManifiesto (self):
		cartaporteNumber = self.numero
		try:
			manifiesto = appMci.models_docmci.Manifiesto.objects.get (cartaporte=self.id)
			return True
		except appMci.models_docmci.Manifiesto.DoesNotExist:
			print (f"+++ No existe manifiesto para cartaporte nro: '{cartaporteNumber}´")
			return False

	#---------------------------------------------------------------
	# Get/Set txt fields
	#---------------------------------------------------------------
	def getTxtRemitente (self):
		cliente = Scripts.getSaveClienteInstanceFromText (self.getTxt ("txt02"), type="02_Remitente")
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


