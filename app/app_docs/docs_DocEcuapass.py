"""
General class for handling documents for cartaporte, manifiesto, declaracion
"""

import uuid
from django.urls import resolve   # To get calling URLs

from ecuapassdocs.utils.resourceloader import ResourceLoader 
from ecuapassdocs.info.ecuapass_utils import Utils

from app_cartaporte.models_doccpi import Cartaporte
from app_manifiesto.models_docmci import Manifiesto, ManifiestoForm
from app_declaracion.models_docdti import Declaracion, DeclaracionForm
from ecuapassdocs.utils.models_scripts import Scripts

class DocEcuapass:
	def __init__ (self, docType, paramsFile):
		print (f"\n+++ Creando nuevo DocEcuapass...")
		self.docType     = docType
		self.inputParams = ResourceLoader.loadJson ("docs", paramsFile) # txt01: ecudocField:---, maxChars:---, value:""
		self.ModelCLASS  = self.getDocModelCLASS ()   

		self.formFields = {k:"" for k in self.inputParams.keys()} # id, numero, usuario, empresa, ..., txt01:xxx, txt02:yyy, ...

	#-------------------------------------------------------------------
	# Print all instance variables
	#-------------------------------------------------------------------
	def printInfo (self):
		print (f"\n+++ Info current doc:'")
		for key, value in vars (self).items():
			print(f"\n\t{key}: {value}")
		
	#-------------------------------------------------------------------
	# Update from view form fields
	#-------------------------------------------------------------------
	def update (self, request, args, kwargs):
		self.id       = ""
		self.numero   = ""
		self.usuario  = request.user.username
		self.empresa  = request.empresa.nickname
		self.pais     = request.session.get ("pais") 
		self.url      = resolve (request.path_info).url_name

		pk            = kwargs.get ('pk')
		if pk:
			self.id = pk

		# Fill formFields
		self.formFields = self.createFormFields ()
		if request.POST:
			requestFields = request.POST
			self.id       = requestFields ["id"]
			self.numero   = requestFields ["numero"]
			fields = ["id", "numero", "usuario", "empresa", "pais", "url"]
			for f in fields:
				self.formFields [f] = requestFields [f]

			for key in [x for x in requestFields.keys() if x.startswith ("txt")]:
				self.formFields [key] = requestFields [key].replace ("\r\n", "\n")

		self.docParams  = self.getDocParamsFromFormFields (self.formFields)
		return self.docParams

	#-- Update from formFields
	def updateFromFormFields (self, formFields):
		fields = ["id", "numero", "usuario", "empresa", "pais", "url"]
		for key in fields:
			setattr (self, key, formFields [key])
		self.formFields = formFields

	#----------------------------------------------------------------
	# Return current form fields
	def getFormFields (self):
		return self.formFields

	def getTxtFields (self):
		txtFields = {}
		for key, value in self.formFields.items ():
			if key.startswith ("txt"):
				txtFields [key] = value
		return txtFields

	#-------------------------------------------------------------------
	# Save new or existing doc to DB
	#-------------------------------------------------------------------
	def saveDocumentToDB (self):
		id, numero = None, None
		if "NUEVO" in self.numero: 
			id = self.saveNewDocToDB ()
		elif "CLON" in self.numero:     
			pass
		else:                                         # Save new doc
			id = self.saveExistingDocToDB ()

		return id 

	#-- Save new document ----------------------------------------------
	def saveDocumentNewToDB  (self):
		print  (f">>> Guardando '{self.docType}' nuevo en la BD...")
		self.numero = self.generateDocNumberFinal ()      # Fist, generate docNumber based on id of last ModelCLASS row"
		docInstance = self.ModelCLASS ()
		docInstance.update  (doc=self)
		return docInstance.id

	#-- Save existing document -----------------------------------------
	def saveDocumentExistingToDB (self):
		print (f"+++\t Guardando '{self.docType}' existente en la BD...")
		docInstance = Scripts.getDocumentById (self.ModelCLASS, self.id)
		docInstance.update  (doc=self)

		# When the document was sugested by predictios
		if self.numero == "SUGERIDO":
			docNumber = Scripts.generateDocNumber (DocModel, self.pais)
			docModel.numero     = docNumber
			formModel.numero    = docNumber
			docFields ["txt00"] = docNumber

		return docInstance.id

	#-------------------------------------------------------------------
	#-- Return form document class and register class from document type
	#-------------------------------------------------------------------
	def getDocModelCLASS  (self):
		import app_cartaporte, app_manifiesto, app_declaracion
		if self.docType == "CARTAPORTE":
			return app_cartaporte.models_doccpi.Cartaporte
		elif self.docType == "MANIFIESTO":
			return app_manifiesto.models_docmci.Manifiesto
		elif self.docType == "DECLARACION":
			return app_declaracion.models_docdti.Declaracion 
		else:
			raise Exception  (f"Error: Tipo de documento '{docType}' no soportado")

	#-------------------------------------------------------------------
	#-- Generate doc number from last doc number saved in DB
	#-------------------------------------------------------------------
	#-- Generate temporal doc number
	def generateDocNumberTemporal  (self):
		docType  = Utils.getDocPrefix (self.docType)
		return  f"NUEVO-{docType}-{str(uuid.uuid4())}"

	#-- Generate final doc number
	def generateDocNumberFinal  (self):
		docType  = Utils.getDocPrefix (self.docType)
		num_zeros = 5
		lastDoc   = self.ModelCLASS.objects.filter  (pais=self.pais).exclude  (numero="SUGERIDO").order_by  ("-id").first  ()
		if lastDoc:
			lastNumber = Utils.getNumberFromDocNumber  (lastDoc.numero)
			newNumber  = str  (lastNumber + 1).zfill  (num_zeros)
		else:
			newNumber  = str  (1).zfill  (num_zeros)

		docNumber = Utils.getCodigoPaisFromPais  (self.pais) + newNumber
		return docNumber

	#-------------------------------------------------------------------
	# Get/Set doc class fiels
	#-------------------------------------------------------------------
	def getDocNumero (self):
		return self.numero if self.numero else ""

	def getDocTitulo (self):
		docTitle   = Utils.getDocPrefix (self.docType) + " : " + self.getDocNumero ()
		return docTitle

	def getDocPais (self):
		return self.pais

	# Get doc from DB. Return doc params -- e.g. txt01: {id,numero,pais,txt01 {align,class,ecudocField,...,value}
	def getExistingDocumentFromDB (self, idRecord):
		record      = self.ModelCLASS.objects.filter (id=idRecord).first()
		docParams   = record.getDocParams (self.inputParams)
		formFields  = self.getFormFieldsFromDocParams (docParams)
		return formFields

	#----------------------------------------------------------------
	# Getters/Settes/Converter between fields (formFields, docParams)
	#----------------------------------------------------------------
	#-- Create empty formFields with all keys of inputParams
	def createFormFields (self):
		return self.getFormFieldsFromDocParams (self.inputParams)

	def getFormFieldsFromDocParams (self, docParams):
		formFields = {}
		for k, v in docParams.items ():	# Not include "numero" and "id"
			formFields [k] = v ["value"]
		return formFields

	def getFormFieldsFromDB (self, idRecord):
		record      = self.ModelCLASS.objects.filter (id=idRecord).first()
		docParams   = record.getDocParams (self.inputParams)
		formFields  = self.getFormFieldsFromDocParams (docParams)
		return formFields

	def getFormFieldsFromRequest (self, request):
		print (f"\n+++ ...getFormFieldsFromRequest...")
		formFields = {}

		formFields ["usuario"] = request.user.username
		formFields ["empresa"] = request.empresa.nickname
		formFields ["pais"]    = request.session.get ("pais") 
		formFields ["url"]     = resolve (request.path_info).url_name

		if request.POST:
			formFields ["id"]      = request.POST.get ("id") 
			formFields ["numero"]  = request.POST.get ("numero") 
			requestValues          = request.POST 
			for key in [x for x in requestValues if x.startswith ("txt")]:
				formFields [key] = requestValues [key].replace ("\r\n", "\n")

		return formFields

	#-- Return docParams from form fields
	def getDocParamsFromFormFields (self, formFields):
		docKeys = ["id", "numero", "pais", "usuario", "empresa"]
		docParams = self.inputParams
		for k in docKeys:
			docParams [k]["value"] = formFields [k]

		for k in formFields.keys():	
			docParams [k]["value"] = formFields [k]
		self.docParams = docParams
		return docParams

	def getDocParams (self, idRecord=None):
		# Check if new or existing document
		if idRecord:
			print (f"\n+++  Cargando documento desde la BD...'")
			self.docParams = self.getSavedDocParams (idRecord)
		else:
			print (f"\n+++  Creando documento nuevo...'")
			self.docParams = self.inputParams

		return self.docParams

	#-------------------------------------------------------------------
	# Get values from DB or initialize document
	#-------------------------------------------------------------------
	# Return logical fields: e.g. 01_Transportista, 02_Remitente, ...
	def getDocFields (self):
		docFields = {}
		for key,value in self.formFields.items ():
			if key.startswith ("txt"):
				docKey = self.inputParams [key]["ecudocsField"]
				docFields [docKey] = value

		return docFields

	#-- Get values from DB into docParams
	def getSavedDocParams (self, idRecord):
		instanceDoc = ModelCLASS.objects.get (id=idRecord)

		# Align text in fields with newlines 
		docParams = self.inputParams
		txtFields = instanceDoc.getTxtFields ()
		print (f"\n+++ {txtFields=}'")

		for k, v in txtFields.items ():	# Not include "numero" and "id"
			text     = txtFields [k]
			maxChars = self.inputParams [k]["maxChars"]
			newText  = Utils.breakLongLinesFromText (text, maxChars)
			docParams [k]["value"] = newText if newText else ""

		return docParams

	#-- Save suggested manifiesto
	#-- TO OPTIMIZE: It is similar to EcuapassDocView::saveNewDocToDB
	def saveSuggestedManifiesto (self, cartaporteDoc, docFields):
		print ("+++ Guardando manifiesto sugerido en la BD...")
		print ("+++ Pais:", self.pais, ". Usuario:", self.usuario)
		# First: save DocModel
		docModel        = Manifiesto (pais=self.pais, usuario=self.usuario)
		docModel.numero = "SUGERIDO"
		docModel.save ()

		# Second, save FormModel
		formModel = ManifiestoForm (id=docModel.id, numero=docModel.numero)
		docFields ["txt00"] = formModel.numero

		# Third, set FormModel values from input form values
		for key, value in docFields.items():
			if key not in ["id", "numero"]:
				setattr (formModel, key, value)

		# Fourth, save FormModel and update DocModel with FormModel
		formModel.save ()
		docModel.documento  = formModel
		docModel.cartaporte = cartaporteDoc
		docModel.save ()
		return docModel

