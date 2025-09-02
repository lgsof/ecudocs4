"""
General class for handling documents for cartaporte, manifiesto, declaracion
"""

from django.urls import resolve   # To get calling URLs
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse

from ecuapassdocs.utils.resourceloader import ResourceLoader 
from ecuapassdocs.info.ecuapass_utils import Utils
from ecuapassdocs.utils.docutils import DocUtils
from app_usuarios.models import Usuario

from app_cartaporte.models_doccpi import Cartaporte
from app_manifiesto.models_docmci import Manifiesto, ManifiestoForm
from app_declaracion.models_docdti import Declaracion, DeclaracionForm
from ecuapassdocs.utils.models_scripts import Scripts
from .pdfcreator import CreadorPDF 

class DocEcuapass:
	def __init__ (self, docType, paramsFile):
		self.docType     = docType
		self.inputParams = ResourceLoader.loadJson ("docs", paramsFile) # txt01: ecudocField:---, maxChars:---, value:""
		self.docModel    = self.getDocModelClass ()

		self.numero      = None
		self.usuario     = None
		self.empresa     = None
		self.pais        = None
		self.url         = None

		self.formFields  = None         # txt01:xxx, txt02:yyy, ...
		self.docFields   = None         # 01_Transportista:xxx, 02_Remitente:yyy, ...
		self.docParams   = None         # txt01: ecudocField:---, maxChars:---, value:XXXX

	#-------------------------------------------------------------------
	# Update parameter fields from current session for any interaction
	#-------------------------------------------------------------------
	def updateFromRequest (self, request):
		print (f"\n+++ ...updateFromRequest...'")
		self.usuario    = request.user
		self.empresa    = request.empresa
		self.pais       = request.session.get ("pais")
		self.url        = resolve (request.path_info).url_name
		self.formFields = self.getFormFieldsFromRequest (request)

	def printInfo (self):
		print ("Document info:")
		print (f"\t+++ {self.usuario=}'")
		print (f"\t+++ {self.empresa=}'")
		print (f"\t+++ {self.pais=}'")
		print (f"\t+++ {self.url=}'")
		print (f"\t+++ {self.formFields=}'")

	#-------------------------------------------------------------------
	# Save new or existing doc to DB
	#-------------------------------------------------------------------
	def saveDocumentToDB (self):
		id, numero = None, None
		if not self.numero or self.numero == "CLON":
			id, numero = self.saveNewDocToDB ()
		else:
			id, numero = self.saveExistingDocToDB ()

		return id, numero

	#-- Save new document ----------------------------------------------
	def saveNewDocToDB  (self):
		print  (f">>> Guardando '{self.docType}' nuevo en la BD...")
		docNumber   = self.generateDocNumber (self.docModel)      # Fist, generate docNumber based on id of last DocModel row"
		docInstance = self.docModel ()
		docInstance.save  (self, docNumber)
		return docInstance.id, docInstance.numero

	#-- Save existing document -----------------------------------------
	def saveExistingDocToDB (self):
		print (f">>> Guardando '{self.docType}' existente en la BD...")
		FormModel, DocModel = DocUtils.getFormAndDocClass (self.docType)

		docId	            = self.formFields ["id"]
		docNumber           = self.formFields ["numero"]
		formModel           = get_object_or_404 (FormModel, id=docId)
		docModel            = get_object_or_404 (DocModel, id=docId)

		# When the document was sugested by predictios
		if docNumber == "SUGERIDO":
			docNumber = Scripts.generateDocNumber (DocModel, self.pais)
			docModel.numero     = docNumber
			formModel.numero    = docNumber
			docFields ["txt00"] = docNumber

		# Assign values to formModel from form values
		for key, value in self.formFields.items():
			if key not in ["id", "numero"]:
				setattr (formModel, key, value)

		docModel.setValues (formModel, self.docFields, self.pais, self.usuario)
		formModel.save ()
		docModel.save ()

		return formModel, docModel

	#-------------------------------------------------------------------
	#-- Return form document class and register class from document type
	#-------------------------------------------------------------------
	def getDocModelClass  (self):
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
	def generateDocNumber  (self, DocModel):
		num_zeros = 5
		lastDoc   = DocModel.objects.filter  (pais=self.pais).exclude  (numero="SUGERIDO").order_by  ("-id").first  ()
		if lastDoc:
			lastNumber = Utils.getNumberFromDocNumber  (lastDoc.numero)
			newNumber  = str  (lastNumber + 1).zfill  (num_zeros)
		else:
			newNumber  = str  (1).zfill  (num_zeros)

		docNumber = Utils.getCodigoPaisFromPais  (self.pais) + newNumber
		print  (f"+++ docNumber '{docNumber}'")
		return docNumber









#	#-------------------------------------------------------------------
#	# Update main parameter fields from current session
#	#-------------------------------------------------------------------
#	def updateDocumentFields (self, sessionFields):
#		print (f"\n+++ updateSessionParams...'")
#		self.pais        = sessionFields ["pais"]
#		self.usuario     = sessionFields ["usuario"]
#		self.empresa     = sessionFields ["empresa"]
#		self.url         = sessionFields ["url"]
#
#		self.formFields  = sessionFields ["formFields"]
#		self.docFields	 = self.getDocFields ()
#
	#-------------------------------------------------------------------
	# Get values from DB or initialize document
	#-------------------------------------------------------------------
	# Return logical fields: e.g. 01_Transportista, 02_Remitente, ...
	def getDocFields (self):
		docFields = {}
		for key, value in self.formFields.items ():
			docKey = self.inputParams [key]["ecudocsField"]
			docFields [docKey] = value
		return docFields

	# Return document params -- e.g. txt01: {id,numero,pais,txt01 {align,class,ecudocField,...,value}
	def getDocParams (self, recordId):
		# Check if new or existing document
		if recordId:
			self.docParams = self.getSavedDocParams (recordId)
		else:
			self.inputParams ["txt0a"]["value"] = Utils.getCodigoPaisFromPais (self.pais)

		return self.inputParams
	
	#-- Return all doc form fiels: txt01, txt02, ...
	def getFormFieldsFromRequest (self, request):
		formFields = {}
		requestValues = request.POST 
		for key in [x for x in requestValues if x.startswith ("txt")]:
			formFields [key] = requestValues [key].replace ("\r\n", "\n")
		return formFields

	#-- Get values from DB into inputParams
	def getSavedDocParams (self, recordId):
		instanceDoc = None
		if (self.docType.upper() == "CARTAPORTE"):
			instanceDoc = Cartaporte.objects.get (id=recordId)
		elif (self.docType.upper() == "MANIFIESTO"):
			instanceDoc = ManifiestoForm.objects.get (id=recordId)
		elif (self.docType.upper() == "DECLARACION"):
			instanceDoc = DeclaracionForm.objects.get (id=recordId)
		else:
			print (f"Error: Tipo de documento '{self.docType}' no soportado")
			return None

		# Align text in fields with newlines 
		docParams = self.inputParams
		txtFields = instanceDoc.get_txt_fields ()

		for k, v in txtFields.items ():	# Not include "numero" and "id"
			text     = txtFields [k]
			maxChars = self.inputParams [k]["maxChars"]
			newText  = Utils.breakLongLinesFromText (text, maxChars)
			docParams [field.name]["value"] = newText if newText else ""

		return docParams

	#-------------------------------------------------------------------
	# Handle assigned documents for "externo" user profile
	#-------------------------------------------------------------------
	#-- Return if user has reached his max number of asigned documents
	def checkLimiteDocumentos (self, usuario, docType):
		user = get_object_or_404 (Usuario, username=usuario)
		print (f"+++ User: '{usuario}'. '{docType}'.  Creados: {user.nro_docs_creados}. Asignados: {user.nro_docs_asignados}")
		
		if (user.perfil == "externo" and user.nro_docs_creados	>= user.nro_docs_asignados):
			return True

		return False

	#-- Only for "cartaportes". Retrieve the object from the DB, increment docs, and save
	def actualizarNroDocumentosCreados (self, usuario, docType):
		if (docType.upper() != "CARTAPORTE"):
			return

		user = get_object_or_404 (Usuario, username=usuario)
		user.nro_docs_creados += 1	# or any other value you want to increment by
		user.save()		

	#-------------------------------------------------------------------
	#-- Create or update suggested Manifiesto according to Cartaporte values
	#-------------------------------------------------------------------
#	def createUpdateSuggestedManifiesto (self, cartaporteDoc):
#		if cartaporteDoc.hasManifiesto ():
#			return
#
#		print ("+++ Creando manifiesto sugerido. ")
#		cartaporteForm  = cartaporteDoc.documento    # CPI form
#		manifiestoInfo  = cartaporteForm.getManifiestoInfo (self.empresa, self.pais)
#		docFields       = ManifiestoForm.getInputValuesFromInfo (manifiestoInfo)
#		self.saveSuggestedManifiesto (cartaporteDoc, docFields)

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

#	#-------------------------------------------------------------------
#	#-- Create a PDF from document
#	#-------------------------------------------------------------------
#	def createPdfResponseSingleDoc (self, pdfType):
#		try:
#			print ("+++ Creando respuesta PDF simple...")
#			creadorPDF = CreadorPDF ("ONE_PDF")
#			outPdfPath = creadorPDF.createPdfDocument (self.docType, self.formFields, pdfType)
#			return self.createPdfResponse (outPdfPath)
#		except Exception as ex:
#			Utils.printException ("Error creando PDF simple")
#		return None
#
#	#-------------------------------------------------------------------
#	# Create PDF for 'Cartaporte' plus its 'Manifiestos'
#	#-------------------------------------------------------------------
#	def createPdfResponseMultiDoc (self, docFields):
#		try:
#			print ("+++ Creando respuesta PDF múltiple...")
#			creadorPDF = CreadorPDF ("MULTI_PDF")
#
#			# Get docFields for Cartaporte childs
#			id = docFields ["id"]
#			valuesList, typesList = self.getInputValuesForDocumentChilds (self.docType, id)
#			inputValuesList		  = [docFields] + valuesList
#			docTypesList		  = [self.docType] + typesList
#
#			outPdfPath = creadorPDF.createMultiPdf (inputValuesList, docTypesList)
#			return self.createPdfResponse (outPdfPath)
#		except Exception as ex:
#			Utils.printException ("Error creando PDF múltiple")
#		return None
#
#	#-------------------------------------------------------------------
#	# Create PDF for 'Cartaporte' plus its 'Manifiestos'
#	#-------------------------------------------------------------------
#	def getInputValuesForDocumentChilds (self, docType, docId):
#		outInputValuesList = []
#		outDocTypesList    = []
#		try:
#			regCartaporte	= Cartaporte.objects.get (id=docId)
#			regsManifiestos = Manifiesto.objects.filter (cartaporte=regCartaporte)
#
#			for reg in regsManifiestos:
#				docManifiesto  = ManifiestoForm.objects.get (id=reg.id)
#				docFields = model_to_dict (docManifiesto)
#				docFields ["txt41"] = "COPIA"
#
#				outInputValuesList.append (docFields)
#				outDocTypesList.append ("MANIFIESTO")
#		except Exception as ex:
#			Utils.printException ()
#			#print (f"'No existe {docType}' con id '{id}'")
#
#		return outInputValuesList, outDocTypesList
#
#	#-- Create PDF response
#	def createPdfResponse (self, outPdfPath):
#		with open(outPdfPath, 'rb') as pdf_file:
#			pdfContent = pdf_file.read()
#
#		# Prepare and return HTTP response for PDF
#		pdfResponse = HttpResponse (content_type='application/pdf')
#		pdfResponse ['Content-Disposition'] = f'inline; filename="{outPdfPath}"'
#		pdfResponse.write (pdfContent)
#
#		return pdfResponse
	
