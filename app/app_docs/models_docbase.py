"""
Base model for doc models: Cartaporte, Manifiesto, Declaracion
"""

from datetime import date

from django.db import models
from django.urls import reverse
from django.http import HttpResponse

from ecuapassdocs.info.ecuapass_utils import Utils 
from ecuapassdocs.utils.models_scripts import Scripts
from ecuapassdocs.info.ecuapass_extractor import Extractor 

from django.db.models import Q, CharField, TextField, EmailField, SlugField, URLField
from django.db.models.functions import Cast

#from .models_Entidades import Cliente

#--------------------------------------------------------------------
# Base model for doc models: Cartaporte, Manifiesto, Declaracion
#--------------------------------------------------------------------
class DocBaseModel (models.Model):
	numero         = models.CharField (max_length=50)
	usuario        = models.ForeignKey ('app_usuarios.Usuario', on_delete=models.SET_NULL, null=True, blank=True)
	empresa        = models.ForeignKey('app_usuarios.Empresa', on_delete=models.CASCADE)
	pais           = models.CharField (max_length=30)
	descripcion    = models.TextField (null=True, blank=True)       # Descripcion
	referencia     = models.CharField (max_length=50, null=True, blank=True)
	fecha_emision  = models.DateField (null=True, blank=True)
	fecha_creacion = models.DateTimeField (auto_now_add=True)

	# TODOS los campos del formulario en formato txt## van aquí
	# Ej: {"txt00": "...", "txt01": "...", "txt13_1": "...", ...}
	txtFields = models.JSONField (default=dict, blank=True)	

	class Meta:
		abstract = True

	#-- Get str for printing-----------------------------------------
	def __str__ (self):
		return f"{self.numero}, {self.fecha_emision}"

	def printInfo (self):
		print (f"\n+++ Info current model:'")
		for field in self._meta.get_fields():
			if hasattr(self, field.name):
				value = getattr(self, field.name)
				print(f"{field.name}: {value}")

	#-- Update base fields using doc info----------------------------
	def update (self, doc):
		# Set basic fields
		self.numero        = doc.numero
		empresaInstance    = Scripts.getEmpresaByNickname (doc.empresa)
		self.empresa       = empresaInstance
		usuarioInstance    = Scripts.getUsuarioByUsernameEmpresa (doc.usuario, empresaInstance.id)
		self.usuario       = usuarioInstance
		self.pais          = doc.pais

		# Set txt fields
		self.setTxtFields (doc.getTxtFields ())
		self.setTxtNumero (self.numero)
		self.setTxtPais (self.pais)

		# Set doc fields
		self.descripcion   = self.getTxtDescripcion ()
		self.fecha_emision = self.getTxtFechaEmision ()

	#-- Save and create response after saving
	def saveCreateResponse (self):
		self.save()
		resp = HttpResponse("OK")
		resp["HX-Trigger"] = '{"docs-updated": true}'
		return resp

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

	#-- Returns the url to access a particular language instance
	def get_absolute_url (self):
		urlName = f"{self.getDocName()}-editardoc"    # e.g. cartaporte-editardoc
		return reverse (urlName, args=[str(self.id)])

	#-- Returns: CARTAPORTE, MANIFIESTO or DECLARACION 
	def getDocType(self):
		return self.__class__.__name__.upper ()

	#-- Return: "cartaporte", "manifiesto" or "declaracion")
	def getDocName(self):
		return self.getDocType ().lower ()

	def getPdfName(self):
		docPrefix = Utils.getDocPrefix (self.getDocType())
		return f"{docPrefix}-{self.numero}.pdf"

	#----------------------------------------------------------------
	# Get/Set txt form fields
	#----------------------------------------------------------------
	def setTxtNumero (self, numero):
		self.setTxt ("txt00", numero)

	def setTxtPais (self, pais):
		self.setTxt ("txt0a", Utils.getCodigoPaisFromPais (pais))

	def getTxtDescripcion (self):
		try:
			docKeys	= {"CARTAPORTE":"txt12", "MANIFIESTO":"txt29", "DECLARACION":"txt10"}
			text    = self.getTxt (docKeys [self.getDocType()])
			return	Extractor.getDescription (text) if text else None
		except Exception as ex:
			Utils.printException (f"Error obteniendo fecha emision para '{self.getDocType()}'")
		return None

	#-- Extract 'fecha emision' from doc fields
	def getTxtFechaEmision (self):
		try:
			docKeys	= {"CARTAPORTE":"txt19", "MANIFIESTO":"txt40", "DECLARACION":"txt23"}
			text    = self.getTxt (docKeys [self.getDocType()])
			return Extractor.getFechaEmisionFromText (text) if text else None
		except Exception as ex:
			Utils.printException (f"Error obteniendo fecha emision para '{self.getDocType()}'")
		return None

	#----------------------------------------------------------------
	# Helpers for get/set form txt fields
	#----------------------------------------------------------------
	def getTxt (self, key, default=None):
		if not key in self.txtFields:
			return ""
		return self.txtFields.get (key, default)

	def setTxt (self, key, value):
		data           = dict (self.txtFields)
		data [key]     = value
		self.txtFields = data

	def setTxtFields (self, mapping: dict, skip_empty=True):
		"""Actualiza varios txt## de una vez."""
		data = dict (self.txtFields)
		for k, v in mapping.items():
			if not skip_empty or (v not in (None, "", [])):
				data[k] = v
		self.txtFields = data	

	def getTxtFields (self):
		txtFields = dict (self.txtFields)
		return txtFields

	#----------------------------------------------------------------
	# Set base values to document. Overwritten in child classes
	#----------------------------------------------------------------
	def setValues (self, docFields, pais, username):
		# Base values
		self.numero     = formModel.numero
		self.pais       = pais
		self.usuario    = self.getUserByUsername (username)

		try:
			self.referencia = docFields ["referencia"]
		except:
			self.referencia = None

	#-- Return user instance by username
	def getUserByUsername (self, username):
		user = Usuario.objects.get (username=username)
		return user

	#-------------------------------------------------------------------
	# Methods for special column "Acciones" when listing documents
	#-------------------------------------------------------------------
	def get_link_editar(self):
		docUrl = self.getDocType ().lower()
		url     = f"{docUrl}-editardoc"
		return reverse (url, args=[self.pk])

	def get_link_pdf (self):
		docUrl = self.getDocType ().lower()
		url     = f"{docUrl}-pdf"
		return reverse (url, args=[self.getPdfName ()])

	def get_link_eliminar(self):
		docUrl = self.getDocType ().lower()
		url     = f"{docUrl}-delete"
		return reverse (url, args=[self.pk])

	def get_link_detalle(self):
		docUrl = self.getDocType ().lower()
		url     = f"{docUrl}-detalle"
		return reverse (url, args=[self.pk])

	
	#-------------------------------------------------------------------
	#-- Search a pattern in all 'FORMMODEL' fields of a model
	#-- Overwritten in some child classes
	#-------------------------------------------------------------------
	def searchModelAllFields(self, s: str):
		M = type(self)

		q = Q()
		for f in M._meta.get_fields():
			if getattr(f, "concrete", False) and not f.is_relation:
				if isinstance(f, (CharField, TextField, EmailField, SlugField, URLField)):
					q |= Q(**{f"{f.name}__icontains": s})

		# Always present on this model → no need to guard
		return (
			M.objects
			 .annotate(_txt=Cast("txtFields", TextField()))
			 .filter(q | Q(_txt__icontains=s))
		)

