import re

from django.db import models

from ecuapassdocs.info.ecuapass_extractor import Extractor

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

	# TODOS los campos del formulario en formato txt## van aquí
	# Ej: {"txt00": "...", "txt01": "...", "txt13_1": "...", ...}
	txtFields = models.JSONField (default=dict, blank=True)	

	# ---------------- Helpers --------------------------------------
	#-- Get str for printing
	def __str__ (self):
		remitente = self.txtFields.get ("txt02") or self.remitente or "-"
		return f"{self.numero}, {remitente}"

	# ---------------------------------------------------------------
	# Save doc to DB
	# ---------------------------------------------------------------
	def save (self, doc, docNumber=None):
		print (f"\n+++ Saving Cartaporte number: '{docNumber}'")
		if docNumber:
			self.numero  = docNumber
			self.usuario = doc.usuario
			self.empresa = doc.empresa
			self.pais    = doc.pais

			docFields      = doc.getDocFields ()
			self.remitente = self.getDocRemitente (docFields)  
			super().save()

	#-- Get/Set txt form fields
	def get_txt (self, key, default=None):
		return self.txtFields.get (key, default)

	def set_txt (self, key, value):
		data       = dict (self.txtFields)
		data [key] = value
		self.txtFields   = data

	def set_txt_fields (self, mapping: dict, skip_empty=True):
		"""Actualiza varios txt## de una vez."""
		data = dict (self.txtFields)
		for k, v in mapping.items():
			if not skip_empty or (v not in (None, "", [])):
				data[k] = v
		self.txtFields = data	

	def get_txt_fields (self):
		txtFields = dict (self.txtFields)
		return txtFields

	def getRemitente(self):
		return self.txtFields.get ("txt02")

	def getDestinatario(self):
		return self.txtFields.get ("txt03")

	def getMercanciaInfo(self):
		return {
			"cantidad":   self.txtFields.get("txt10"),
			"marcas":	  self.txtFields.get("txt11"),
			"descripcion": self.txtFields.get("txt12"),
		}	

	def setValues (self, formFields, docFields, pais, username):
		# Base values
		self.pais = pais
		self.descripcion   = self.getDocDescripcion (docFields)
		self.fecha_emision = self.getDocFechaEmision (docFields)

		# Document values
		self.remitente     = self.getDocRemitente (docFields)
		self.destinatario  = self.getDocDestinatario (docFields)

		# Mezcla todos los txt## que vengan
		only_txt = {k: v for k, v in formFields.items() if str (k).startswith("txt")}
		self.set_txt_fields (only_txt)		
		
		# If not has, then create "suggested" manifiesto
		#self.createUpdateSuggestedManifiesto ()

	#-- Check if the CPI has a "manifiesto"
	def hasManifiesto (self):
		cartaporteNumber = self.numero
		try:
			manifiesto = appMci.models_docmci.Manifiesto.objects.get (cartaporte=self.id)
			return True
		except appMci.models_docmci.Manifiesto.DoesNotExist:
			print (f"+++ No existe manifiesto para cartaporte nro: '{cartaporteNumber}´")
			return False

	def getDocRemitente (self, docFields):
		cliente = Scripts.getSaveClienteInstanceFromText (docFields ["02_Remitente"], type="02_Remitente")
		print (f"\n+++ {cliente=}'")
		return cliente 

	def getDocDestinatario (self, docFields):
		clienteInfo = Scripts.getSaveClienteInstanceFromText (docFields ["03_Destinatario"], type="03_Destinatario")
		return clienteInfo

	def getDocDescripcion (self, docFields):
		return docFields ["12_Descripcion_Bultos"]

	#----------------------------------------------------------------
	#-- Old form fields
	#----------------------------------------------------------------
#	def getNumberFromId (self):
#		numero = 2000000+ self.numero 
#		numero = f"CI{numero}"
#		return (self.numero)
#
#	def getNumero (self):
#		return self.txt00
#	def getRemitente (self):
#		return self.txt02
#	def getDestinatario (self):
#		return self.txt03
#
#	def getMercanciaInfo (self):
#		return {"cantidad":self.txt10, "marcas":self.txt11, "descripcion":self.txt12}
#
#	#-- Get info from CartaporteForm itself, empresa, pais, and predictions
#	def getManifiestoInfo (self, empresa, pais):
#		empresaInfo = EcuData.empresas [empresa]
#
#		# Info from Empresa, pais
#		info = {}
#		info ["pais"]               = pais[:2]
#		info ["permisoOriginario"]  = empresaInfo ["permisos"]["originario"]
#		info ["permisoServicios"]   = empresaInfo ["permisos"]["servicios1"]
#
#		aduanasDic = { "COLOMBIA": {"aduanaCruce":"IPIALES-COLOMBIA", "aduanaDestino":"TULCAN-ECUADOR"},
#			           "ECUADOR" : {"aduanaCruce":"TULCAN-ECUADOR", "aduanaDestino":"IPIALES-COLOMBIA"},
#			           "PERU"    : {"aduanaCruce":"", "aduanaDestino":""} }
#		info.update (aduanasDic [pais])
#
#		# Info from Cartaporte
#		info ["cartaporte"]         = self.numero
#		info ["cantidad"]           = self.txt10
#		info ["marcas"]             = self.txt11
#		info ["descripcion"]        = self.txt12
#		info ["pesoNeto"]           = self.txt13_1
#		info ["pesoBruto"]          = self.txt13_2
#		info ["volumen"]            = self.txt14
#		info ["otrasUnd"]           = self.txt15
#		info ["incoterms"]          = re.sub (r'[\r\n]+\s*', '. ', self.txt16) # Plain INCONTERMS
#		info ["fechaEmision"]       = self.txt19
#
#		# Info from predicions: vehiculo, carga
##		predInfo  = self.getPredictor ()
##		info.update (predInfo)
#
#		return info
#
#	def getPredictor (self):
#		from app_cartaporte.predictor import Predictor
#		predictor = Predictor ()
#		predInfo  = predictor.predictManifiestoInfo (self)
#		return predInfo
#

