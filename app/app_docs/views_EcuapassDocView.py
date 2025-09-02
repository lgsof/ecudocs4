
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
		super().__init__ (*args, **kwargs)
		self.docType	      = docType
		self.template_name    = "documento_forma.html"
		self.background_image = background_image

		self.doc              = DocEcuapass (docType, parameters_file)
		self.commander        = Commander (self.docType)

	#-------------------------------------------------------------------
	# Usado para llenar una forma (manifiesto) vacia_
	# Envía los parámetros o restricciones para cada campo en la forma de HTML
	#-------------------------------------------------------------------
	def get (self, request, *args, **kwargs):
		print ("\n\n+++ GET : EcuapassDocView +++")
		urlCommand = resolve (request.path_info).url_name
		return self.getResponseForCommand (urlCommand, request, *args, **kwargs)

	#-------------------------------------------------------------------
	# Used to receive a filled manifiesto form and create a response
	# Get doc number and create a PDF from document values.
	#-------------------------------------------------------------------
	@method_decorator(csrf_protect)
	def post (self, request, *args, **kwargs):
		print ("\n\n+++ POST : EcuapassDocView +++")
		buttonCommand  = request.POST.get ('boton_seleccionado', '').lower()
		return self.getResponseForCommand (buttonCommand, request, *args, **kwargs)

	#-------------------------------------------------------------------
	# Get response for document command (save, original, copia, clon, ...)
	#-------------------------------------------------------------------
	def getResponseForCommand (self, command, request, *args, **kwargs):
		response = None
		self.doc.updateFromRequest (request)
		self.doc.printInfo()

		if "guardar" in command:
			docId = self.onSaveCommand (request) 
			return redirect (f"editar/{docId}")
		elif "editar" in command or "nuevo" in command:
			return self.onEditCommand (command, request, *args, **kwargs)
		elif "pdf" in command:
			return self.commander.onPdfCommand (command, request, *args, **kwargs)
		elif "clonar" in command:
			return self.onCloneCommand (command, request, *args, **kwargs)
		else:
			messages.add_message (request, messages.ERROR, f"ERROR: Opción '{command}' no existe")
			response = render (request, 'messages.html')
		return response

	#-------------------------------------------------------------------
	# Edit existing, new, or clon doc
	#-------------------------------------------------------------------
	def onEditCommand  (self, command, request, *args, **kwargs):
		print (f"\n+++ onEditCommand...")
		pk = kwargs.get ('pk')

		self.docParams = self.doc.getDocParams (pk)
			
		# Send input fields parameters (bounds, maxLines, maxChars, ...)
		docUrl     = self.docType.lower()
		docNumber  = self.docParams ["numero"]["value"]
		docTitle   = Utils.getDocPrefix (self.docType) + " : " + docNumber
		contextDic = {
			"docTitle"         : docTitle,
			"docType"          : self.docType, 
			"pais"             : self.doc.pais,
			"input_parameters" : self.docParams, 
			"background_image" : self.background_image,
			"document_url"	   : docUrl,
			"timestamp"        : now().timestamp ()
		}
		return render (request, self.template_name, contextDic)

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
	# Save document to DB checking max docs for user
	#-------------------------------------------------------------------
	def onSaveCommand (self, request, *args, **kwargs):
		print ("+++ Guardando documento...")
		docId, docNumber = self.doc.saveDocumentToDB ()
		return docId

#	#-------------------------------------------------------------------
#	# Update parameter fields from current session for any interaction
#	#-------------------------------------------------------------------
#	def updateDocument (self, request):
#		print (f"\n+++ ...updateDocument...'")
#		self.doc.pais      = request.session.get ("pais")
#		self.doc.usuario   = request.user
#		self.doc.empresa   = request.empresa
#		self.doc.url       = resolve (request.path_info).url_name
#		self.doc.formFiels = self.doc.getFormFieldsFromRequest (request)

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

#	#-------------------------------------------------------------------
#	#-- Set saved or default values to inputs
#	#-------------------------------------------------------------------
#	def copySavedValuesToInputs (self, recordId):
#		instanceDoc = None
#		if (self.docType.upper() == "CARTAPORTE"):
#			instanceDoc = CartaporteForm.objects.get (id=recordId)
#		elif (self.docType.upper() == "MANIFIESTO"):
#			instanceDoc = ManifiestoForm.objects.get (id=recordId)
#		elif (self.docType.upper() == "DECLARACION"):
#			instanceDoc = DeclaracionForm.objects.get (id=recordId)
#		else:
#			print (f"Error: Tipo de documento '{self.docType}' no soportado")
#			return None
#
#		# Iterating over fields
#		for field in instanceDoc._meta.fields:	# Not include "numero" and "id"
#			text = getattr (instanceDoc, field.name)
#			maxChars = self.docParams [field.name]["maxChars"]
#			newText = Utils.breakLongLinesFromText (text, maxChars)
#			self.docParams [field.name]["value"] = newText if newText else ""
#
#		return self.docParams

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

	#---------------------- OBSOLETE -----------------------------------
	#-------------------------------------------------------------------
	#-- Return a dic with the texts from the document form (e.g. txt00,)
	#-------------------------------------------------------------------
#	def getInputValuesFromForm (self, request):
#		inputFields = {}
#		requestValues = request.POST 
#
#		for key in requestValues:
#			if "boton" in key:
#				continue
#
#			inputFields [key] = requestValues [key].replace ("\r\n", "\n")
#
#		return inputFields


