
from django.http import HttpResponseRedirect
from django.urls import reverse


from django.utils.timezone import now
from django.shortcuts import render
from django.views import View

from django.contrib import messages

# For CSRF protection
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

# For login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import resolve   # To get calling URLs

# Own imports
from ecuapassdocs.info.ecuapass_utils import Utils 

from app_manifiesto.models_docmci import Manifiesto, ManifiestoForm
from app_declaracion.models_docdti import Declaracion, DeclaracionForm

from .docs_DocEcuapass import DocEcuapass 
from ecuapassdocs.utils.commander import Commander

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

	return render(request, 'documento_forma_main.html', context)

#--------------------------------------------------------------------
#-- Vista para manejar las solicitudes de manifiesto
#--------------------------------------------------------------------
LAST_SAVED_VALUES = None
class EcuapassDocView (LoginRequiredMixin, View):

	def __init__(self, docType, background_image, parameters_file, *args, **kwargs):
		print (f"\n+++ Creando nueva vista EcuapassDocView...")
		super().__init__ (*args, **kwargs)
		self.docType	      = docType
		self.template_name    = "documento_forma_frame.html"
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
		print (f"\t+++ getResponseForCommand::{request.GET=}'")
		pdfType  = request.GET.get ('pdfType', '').lower()
		urlCommand = resolve (request.path_info).url_name
		return self.getResponseForCommand (urlCommand, request, *args, **kwargs)

	#-------------------------------------------------------------------
	# Used to receive a filled manifiesto form and create a response
	# Get doc number and create a PDF from document values.
	#-------------------------------------------------------------------
	@method_decorator(csrf_protect)
	def post (self, request, *args, **kwargs):
		print ("\n\n+++ POST :: EcuapassDocView +++")
		print (f"\t+++ getResponseForCommand::{request.POST=}'")
		buttonCommand  = request.POST.get ('boton_seleccionado', '').lower()
		return self.getResponseForCommand (buttonCommand, request, *args, **kwargs)

	#-------------------------------------------------------------------
	# Get response for document command (save, original, copia, clon, ...)
	#-------------------------------------------------------------------
	def getResponseForCommand (self, command, request, *args, **kwargs):
		response = None
		self.docParams  = self.doc.update (request, args, kwargs)
		self.formFields = self.doc.getFormFields ()

		if "editar" in command or "nuevo" in command:
			return self.onEditCommand ("NORMAL", request, *args, **kwargs)
		elif "guardar" in command:
			docId = self.onSaveCommand (request, args, kwargs) 
			return HttpResponseRedirect (self.get_edit_url(docId))
		elif "pdf" in command:
			return self.onPdfCommand (command, request, *args, **kwargs)
		elif "clonar" in command:
			return self.onCloneCommand (command, request, *args, **kwargs)
		else:
			messages.add_message (request, messages.ERROR, f"ERROR: Opción '{command}' no existe")
			response = render (request, 'messages.html')
		return response

	#-------------------------------------------------------------------
	# Set "txt00" to "CLON" and call edit without "pk" so with current docParams
	#-------------------------------------------------------------------
	def onCloneCommand  (self, command, request, *args, **kwargs):
		print (f"\n+++ onCloneCommand...")
		pk = kwargs.get ('pk')
		return self.onEditCommand ("CLON", request, args, kwargs)
	
	#-------------------------------------------------------------------
	#-------------------------------------------------------------------
	def onPdfCommand (self, pdfCommand, request, *args, **kwargs):
		print (f"\n+++ onPdfCommand:", request.method, ": PK :", kwargs.get ("pk"))
		if request.method == "GET":
			pk         = int (request.GET.get ("pk"))
			pdfCommand = request.GET.get ("pdfType")
			self.formFields = self.doc.getFormFieldsFromDB (pk)
		else:
			self.formFields = self.doc.getFormFieldsFromRequest (request)

		return self.commander.createPdf (pdfCommand, self.formFields)

	#-------------------------------------------------------------------
	# Save document to DB checking max docs for user
	#-------------------------------------------------------------------
	def onSaveCommand (self, request, *args, **kwargs):
		print ("+++ onSaveCommand...")
		pk  = kwargs.get ('pk')
		docNumber  = self.formFields ["numero"]
		if "NUEVO" in docNumber or "CLON" in docNumber:
			docId = self.doc.saveDocumentNewToDB ()
		else:
			docId = self.doc.saveDocumentExistingToDB ()

		return docId

	#-------------------------------------------------------------------
	# Edit existing, new, or clon doc
	#-------------------------------------------------------------------
	def onEditCommand  (self, editType, request, *args, **kwargs):
		print (f"\n+++ onEditCommand...")
		pk        = kwargs.get ('pk')

		if (editType=="NORMAL" and not pk): # New
			formFields = self.editDocumentNew (request)
		elif (editType=="NORMAL" and pk):   # Existing 
			formFields = self.editDocumentFromDB (request, pk)
		elif (editType=="CLON"):              # Clone
			formFields = self.editDocumentClon (request)

		# Send input fields parameters (bounds, maxLines, maxChars, ...)
		self.doc.updateFromFormFields (formFields)
		docParams = self.doc.getDocParamsFromFormFields (self.formFields)
		contextDic = {
			"docTitle"         : self.doc.getDocTitulo (),
			"docType"          : self.docType, 
			"pais"             : self.doc.getDocPais (),
			"input_parameters" : docParams,
			"background_image" : self.background_image,
			"document_url"	   : self.docType.lower(),
			"timestamp"        : now().timestamp ()
		}
		return render (request, self.template_name, contextDic)

	#-- Update form fields new doc
	def editDocumentNew (self, request):
		print (f"\n+++ Editing new document...'")
		self.formFields ["id"]     = ""
		self.formFields ["numero"] = self.doc.generateDocNumberTemporal ()
		return self.formFields

	#-- Get doc from DB and updates session docs
	def editDocumentFromDB (self, request, pk):
		print (f"\n+++ Editing exising document {pk=}'")
		self.formFields = self.doc.getExistingDocumentFromDB (pk)
		return self.formFields

	def editDocumentClon (self, request):
		print (f"\n+++ Editing cloned document...'")
		self.formFields = self.doc.getFormFieldsFromRequest (request)
		self.formFields ["numero"] = "CLON"
		self.formFields ["txt00"]  = "CLON"
		return self.formFields

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


	#----------------------------------------------------------------
	# Build the URL name you already use for editing.
	# Example: name='cartaporte_editar' with path('cartaporte/editar/<int:pk>/...')
	#----------------------------------------------------------------
	def get_edit_url(self, pk: int) -> str:
		url_name = f"{self.docType.lower()}-editardoc"
		return reverse(url_name, kwargs={"pk": pk})

