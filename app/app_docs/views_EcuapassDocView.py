
import json, os, re, sys
from os.path import join

from django.utils.timezone import now
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views import View

from django.contrib import messages
from django.forms.models import model_to_dict

# For CSRF protection
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

# For login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import resolve   # To get calling URLs

# Own imports
from ecuapassdocs.info.ecuapass_utils import Utils 
from ecuapassdocs.utils.docutils import DocUtils

from app_cartaporte.models_doccpi import Cartaporte
from app_manifiesto.models_docmci import Manifiesto, ManifiestoForm
from app_declaracion.models_docdti import Declaracion, DeclaracionForm

from app_usuarios.models import Usuario

from .pdfcreator import CreadorPDF 
from .docs_DocEcuapass import DocEcuapass 
from ecuapassdocs.utils.models_scripts import Scripts
from .commander import Commander

#--------------------------------------------------------------------
#-- Handle URL request for new doc template with iframes
#-- Basically, render the document template to be put in the iframe
#--------------------------------------------------------------------
def docView(request, *args, **kwargs):
	docType = request.path.strip('/').split('/')[0]
	if "pk" in kwargs:
		context = {"requestType":f"{docType}-editar", "pk":kwargs ["pk"]}
	else:
		context = {f"requestType":f"{docType}-nuevo"}

	return render(request, 'documento_main.html', context)

#--------------------------------------------------------------------
#-- Vista para manejar las solicitudes de manifiesto
#--------------------------------------------------------------------
LAST_SAVED_VALUES = None
class EcuapassDocView (LoginRequiredMixin, View):

	def __init__(self, docType, background_image, parameters_file, *args, **kwargs):
		print (f"\n+++ Creando nueva vista EcuapassDocView...")
		super().__init__ (*args, **kwargs)
		self.docType	      = docType
		self.template_name    = "documento_forma.html"
		self.background_image = background_image
		self.parameters_file  = parameters_file

		self.commander        = Commander (self.docType)
		self.doc              = DocEcuapass (self.docType, self.parameters_file)

	#-------------------------------------------------------------------
	# Usado para llenar una forma (manifiesto) vacia_
	# Envía los parámetros o restricciones para cada campo en la forma de HTML
	#-------------------------------------------------------------------
	def get (self, request, *args, **kwargs):
		print ("\n\n+++ GET :: EcuapassDocView +++")
		urlCommand = resolve (request.path_info).url_name
		return self.getResponseForCommand (urlCommand, request, *args, **kwargs)

	#-------------------------------------------------------------------
	# Used to receive a filled manifiesto form and create a response
	# Get doc number and create a PDF from document values.
	#-------------------------------------------------------------------
	@method_decorator(csrf_protect)
	def post (self, request, *args, **kwargs):
		print ("\n\n+++ POST :: EcuapassDocView +++")
		buttonCommand  = request.POST.get ('boton_seleccionado', '').lower()
		return self.getResponseForCommand (buttonCommand, request, *args, **kwargs)

	#-------------------------------------------------------------------
	# Get response for document command (save, original, copia, clon, ...)
	#-------------------------------------------------------------------
	def getResponseForCommand (self, command, request, *args, **kwargs):
		response = None
		self.getCurrentDocuments (request)

		if "editar" in command or "nuevo" in command:
			return self.onEditCommand (request, *args, **kwargs)
		elif "guardar" in command:
			docId = self.onSaveCommand (request) 
			return redirect (f"editar/{docId}")
		elif "pdf" in command:
			return self.commander.onPdfCommand (command, self.doc, request, *args, **kwargs)
		elif "clonar" in command:
			return self.onCloneCommand (command, request, *args, **kwargs)
		else:
			messages.add_message (request, messages.ERROR, f"ERROR: Opción '{command}' no existe")
			response = render (request, 'messages.html')
		return response

	#-------------------------------------------------------------------
	#-------------------------------------------------------------------
	def onPdfCommand  (self, command, request, *args, **kwargs):
		formFields = self.doc.getFormFieldsFromRequest (request)
		pk        = kwargs.get ('pk')
		if (pk):
			self.docParams  = self.doc.getExistingDocument (pk)
			self.formFields = self.doc.getFormFieldsFromDocParams (self.docParams)
			return self.commander.onPdfCommand (command, request, *args, **kwargs)
	#-------------------------------------------------------------------
	#-- Get/Create current document 
	#-------------------------------------------------------------------
	def getCurrentDocuments (self, request):
		print (f"\n+++ Getting session current documents...'")
		if not "current_docs" in request.session:
			print (f"\n+++ Creating session current documents...'")
			request.session ["current_docs"] = {}

		self.currentDocs = request.session ["current_docs"]

	#-------------------------------------------------------------------
	# Edit existing, new, or clon doc
	#-------------------------------------------------------------------
	def onEditCommand  (self, request, *args, **kwargs):
		print (f"\n+++ onEditCommand...")
		pk        = kwargs.get ('pk')
		if (pk):
			docParams = self.editExistingDocument (request, pk)
		else:
			docParams = self.editNewDocument (request)

		# Send input fields parameters (bounds, maxLines, maxChars, ...)
		docUrl     = self.docType.lower()
		contextDic = {
			"docTitle"         : self.doc.getDocTitulo (),
			"docType"          : self.docType, 
			"pais"             : self.doc.getDocPais (),
			"input_parameters" : docParams,
			"background_image" : self.background_image,
			"document_url"	   : docUrl,
			"timestamp"        : now().timestamp ()
		}
		return render (request, self.template_name, contextDic)


	def editExistingDocument (self, request, pk):
		print (f"\n+++ Editing exising document {pk=}'")
		self.docParams  = self.doc.getExistingDocument (pk)
		self.formFields = self.doc.getFormFieldsFromDocParams (self.docParams)
		request.session ["current_docs"][self.formFields ["numero"]] = self.formFields

		return self.docParams

	def editNewDocument (self, request):
		print (f"\n+++ Editing new document...'")
		formFields                     = self.doc.getFormFields ()

		formFields ["id"]          = ""
		formFields ["numero"]      = self.doc.generateDocNumber ("NEW")
		formFields ["usuario"]     = request.user.username
		formFields ["empresa"]     = request.empresa.nickname
		formFields ["pais"]        = request.session.get ("pais")
		formFields ["url"]         = resolve (request.path_info).url_name
		request.session ["current_docs"][formFields ["numero"]] = formFields

		request.session.modified = True
		self.doc.update (formFields)

		docParams = self.doc.getDocParams ()
		docParams ["numero"]["value"] = formFields ["numero"]
		docParams ["txt00"]["value"] = formFields ["numero"]

		self.currentDocs = request.session ["current_docs"]
		return docParams

	#-------------------------------------------------------------------
	# Save document to DB checking max docs for user
	#-------------------------------------------------------------------
	def onSaveCommand (self, request, *args, **kwargs):
		print ("+++ Guardando documento...")
		print (f"\n+++ {request.POST.get ('txt00')=}'")
		docNumber = request.POST.get ('numero')
		if "NUEVO" in docNumber:
			formFields = self.doc.getFormFieldsFromRequest (request)
			self.doc.update (formFields)
			docId = self.doc.saveNewDocToDB ()
		else:
			formFields = self.doc.getFormFieldsFromRequest (request)
			self.doc.update (formFields)
			docId = self.doc.saveDocumentToDB ()

		return docId

	#-------------------------------------------------------------------
	# Set "txt00" to "CLON" and call edit without "pk" so with current docParams
	#-------------------------------------------------------------------
	def onCloneCommand  (self, command, request, *args, **kwargs):
		print (f"\n+++ onCloneCommand...")
		pk = kwargs.get ('pk')
		self.docParams = self.doc.getDocParams (pk)
		self.docParams ["numero"]['value'] = "CLON"
		self.docParams ["txt00"]['value'] = "CLON"
		return self.onEditCommand (command, request, args, kwargs)
	
	#-------------------------------------------------------------------
	# Check if document has changed
	#-------------------------------------------------------------------
	def hasChangedDocument (self, inputFields):
		global LAST_SAVED_VALUES
		if LAST_SAVED_VALUES == None:
			return True

		for k in inputFields.keys ():
			try:
				current, last = inputFields [k], LAST_SAVED_VALUES [k]

				if current != last:
					print (f"+++ Documento ha cambiado en clave '{k}': '{current}', '{last}'")
					return True
			except Exception as ex:
				print (f"EXCEPCION: Clave '{k}' no existe")

		return False

	#-------------------------------------------------------------------
	#-- Save document to DB if form's values have changed
	#-------------------------------------------------------------------
	def updateDocumentToDB (self, sessionInfo, docSessionParams):
		if self.hasChangedDocumentValues (sessionInfo):
			currentInputValues = sessionInfo.get ("currentInputValues")
			savedtInputValues  = sessionInfo.get ("savedInputValues")
			sessionInfo.set ("savedInputValues", currentInputValues)
			print (sessionInfo)
			self.doc.saveDocumentToDB (currentInputValues)
			self.inputFields = currentInputValues

			return True
		else:
			return False

	#-------------------------------------------------------------------
	# Check if document input values has changed from the saved ones
	#-------------------------------------------------------------------
	def hasChangedDocumentValues (self, sessionInfo):
		print ("+++ DEBUG: hasChangedDocumentValues")
		currentInputValues = sessionInfo.get ("currentInputValues")
		savedInputValues  = sessionInfo.get ("savedInputValues")

		if savedInputValues == None and currentInputValues == None:
			return False
		elif savedInputValues == None:
			return True

		# Check key by key
		for k in currentInputValues.keys ():
			try:
				current, saved = currentInputValues [k], savedInputValues [k]
				if current != saved:
					print (f"+++ Documento ha cambiado en clave '{k}': '{current}', '{last}'")
					print ("+++ DEBUG: hasChangedDocumentValues", len(current), len (last)) 
					print ("+++ DEBUG: hasChangedDocumentValues", type(current), type (last)) 
					return True
			except Exception as ex:
				print (f"EXCEPCION: Clave '{k}' no existe")

		return False


