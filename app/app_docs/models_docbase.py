"""
Base model for doc models: Cartaporte, Manifiesto, Declaracion
"""

from datetime import date

from django.db import models
from django.urls import reverse

from ecuapassdocs.info.ecuapass_utils import Utils 

from django.db.models import Q

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

	class Meta:
		abstract = True

	#-- Get str for printing
	def __str__ (self):
		return f"{self.numero}, {self.fecha_emision}"

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
		docName = self.getDocType ().lower()
		url     = f"{docName}-editardoc"
		return reverse (url, args=[self.pk])

	def get_link_pdf (self):
		docName = self.getDocType ().lower()
		url     = f"{docName}-pdf_original"
		return reverse (url, args=[self.pk])

	def get_link_eliminar(self):
		docName = self.getDocType ().lower()
		url     = f"{docName}-delete"
		return reverse (url, args=[self.pk])

	def get_link_detalle(self):
		docName = self.getDocType ().lower()
		url     = f"{docName}-detalle"
		return reverse (url, args=[self.pk])

	#-------------------------------------------------------------------
	#-- Documents function
	#-------------------------------------------------------------------
	#-- Extract 'fecha emision' from doc fields
	def getDocFechaEmision (self, docFields):
		try:
			keys	= {"CARTAPORTE":"19_Emision", "MANIFIESTO":"40_Fecha_Emision", "DECLARACION":"23_Fecha_Emision"}
			text	= docFields [keys [docType]]
			return Extractor.getFechaEmisionFromText (docFields ["19_Emision"]) 
		except Exception as ex:
			Utils.printException (f"Error obteniendo fecha emision para '{self.docType}'")
		return None

	#-------------------------------------------------------------------
	#-- Search a pattern in all 'FORMMODEL' fields of a model
	#-- Overwritten in some child classes
	#-------------------------------------------------------------------
	def searchModelAllFields (self, searchPattern):
		queries = Q()
		FORMMODEL = self._meta.get_field ('documento').related_model
		for field in FORMMODEL._meta.fields:
			field_name = field.name
			queries |= Q(**{f"{field_name}__icontains": searchPattern})
		
		formInstances = FORMMODEL.objects.filter (queries)
		DOCMODEL      = self.__class__
		docInstances  = DOCMODEL.objects.filter (documento__in=formInstances)
		return docInstances

#	#-------------------------------------------------------------------
#	# DB Functions
#	#-------------------------------------------------------------------
#	def saveNewDocToDB  (doc):
#		print  (f">>> Guardando '{docType}' nuevo en la BD...")
#
#		DocModel  = self.getDocModelClass  (doc.docType)
#		docNumber = self.generateDocNumber (DocModel, doc.pais)      # Fist, generate docNumber based on id of last DocModel row"
#
#		# Second, save doc model
#		docModel  = DocModel (numero=docNumber, pais=doc.pais, usuario=doc.usuario)
#		docModel.save  ()
#
#		return id, docNumber
#
#	#-------------------------------------------------------------------
#	#-- Return form document class and register class from document type
#	#-------------------------------------------------------------------
#	def getDocModelClass  (self):
#		import app_cartaporte, app_manifiesto, app_declaracion
#		if self.docType == "CARTAPORTE":
#			return app_cartaporte.models_doccpi.Cartaporte
#		elif self.docType == "MANIFIESTO":
#			return app_manifiesto.models_docmci.Manifiesto
#		elif self.docType == "DECLARACION":
#			return app_declaracion.models_docdti.Declaracion 
#		else:
#			raise Exception  (f"Error: Tipo de documento '{docType}' no soportado")
#			
#	#-------------------------------------------------------------------
#	#-- Generate doc number from last doc number saved in DB
#	#-------------------------------------------------------------------
#	def generateDocNumber  (self, DocModel, pais):
#		num_zeros = 5
#		lastDoc   = DocModel.objects.filter  (pais=pais).exclude  (numero="SUGERIDO").order_by  ("-id").first  ()
#		if lastDoc:
#			lastNumber = Utils.getNumberFromDocNumber  (lastDoc.numero)
#			newNumber  = str  (lastNumber + 1).zfill  (num_zeros)
#		else:
#			newNumber  = str  (1).zfill  (num_zeros)
#
#		docNumber = Utils.getCodigoPaisFromPais  (pais) + newNumber
#		print  (f"+++ docNumber '{docNumber}'")
#		return docNumber
#
