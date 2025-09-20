
from django.http import HttpResponseRedirect
from django.urls import reverse


from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.views import View

from django.contrib import messages
from django.http import HttpResponse

# For CSRF protection
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

# For login
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import resolve   # To get calling URLs

# Own imports
from ecuapassdocs.info.ecuapass_utils import Utils 

from .docs_DocEcuapass import DocEcuapass 
from ecuapassdocs.utils.docpdfcreator import DocPdfCreator

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
	raise_exception = True  # don't redirect to login, let us handle it

	permission_required = "app_cartaporte.add_cartaporte"  # <— app_label.add_modelname
	def __init__(self, docType, background_image, parameters_file, *args, **kwargs):
		print (f"\n+++ Creando nueva vista EcuapassDocView...")
		super().__init__ (*args, **kwargs)
		self.docType	      = docType
		self.template_name    = "documento_forma_frame.html"
		self.background_image = background_image
		self.parameters_file  = parameters_file

		self.doc              = DocEcuapass (self.docType, self.parameters_file)

	#-------------------------------------------------------------------
	# Usado para llenar una forma (manifiesto) vacia_
	# Envía los parámetros o restricciones para cada campo en la forma de HTML
	#-------------------------------------------------------------------
	def get (self, request, *args, **kwargs):
		print ("\n\n+++ GET :: EcuapassDocView +++")
		print (f"\t+++ getResponseForCommand::{request.GET=}'")
		urlCommand = resolve (request.path_info).url_name
		#return self.handle_no_permission ()
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
	# Run before GET or POST: Check if user can create docs
	#-------------------------------------------------------------------
	def dispatch(self, request, *args, **kwargs):
		if not self.userCanCreateDocs (request):
			return self.handle_no_permission()

		return super().dispatch(request, *args, **kwargs)

	#-------------------------------------------------------------------
	# Get response for document command (save, original, copia, clon, ...)
	#-------------------------------------------------------------------
	def getResponseForCommand (self, command, request, *args, **kwargs):
		self.formFields = self.doc.update (request, args, kwargs)

		if "nuevo" in command:
			return self.onEditCommand ("NUEVO", request, *args, **kwargs)
		elif "editar" in command:
			return self.onEditCommand ("BDATOS", request, *args, **kwargs)
		elif "guardar" in command:
			docId = self.onSaveCommand (request, args, kwargs) 
			return HttpResponseRedirect (self.get_edit_url(docId))
		elif "pdf" in command:
			return self.onPdfCommand (command, request, *args, **kwargs)
		elif "clonar" in command:
			return self.onCloneCommand (command, request, *args, **kwargs)
		else:
			messages.add_message (request, messages.ERROR, f"ERROR: Opción '{command}' no existe")
			return render (request, 'messages.html')

	#-------------------------------------------------------------------
	# Edit existing, new, or clon doc
	#-------------------------------------------------------------------
	def onEditCommand  (self, editType, request, *args, **kwargs):
		print (f"\n+++ onEditCommand...")
		pk        = kwargs.get ('pk')

		if (editType=="NUEVO"): # New
			formFields = self.editDocumentNew (request)
		elif (editType=="BDATOS"):   # Existing 
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
		formFields            = self.doc.getFormFieldsFromRequest (request)
		formFields ["id"]     = ""
		formFields ["numero"] = self.doc.generateDocNumberTemporal ()
		formFields            = self.doc.updateFromFormFields (formFields)
		self.formFields       = formFields

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
	# Set "txt00" to "CLON" and call edit without "pk" so with current docParams
	#-------------------------------------------------------------------
	def onCloneCommand  (self, command, request, *args, **kwargs):
		print (f"\n+++ onCloneCommand...")
		pk = kwargs.get ('pk')
		return self.onEditCommand ("CLON", request, args, kwargs)
	
	#-------------------------------------------------------------------
	#-------------------------------------------------------------------
	def onPdfCommand (self, pdfType, request, *args, **kwargs):
		print (f"\n+++ onPdfCommand:", request.method, ": PK :", kwargs.get ("pk"))
		if request.method == "GET":
			pk      = int (request.GET.get ("pk"))
			pdfType = request.GET.get ("pdfType")
			self.formFields = self.doc.getFormFieldsFromDB (pk)
		else:
			self.formFields = self.doc.getFormFieldsFromRequest (request)

		docPdfCreator = DocPdfCreator (self.docType)
		return docPdfCreator.createPdf (pdfType, self.formFields)

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

	#----------------------------------------------------------------
	# Check and handle when users are not allowed to create docs
	#----------------------------------------------------------------
	#-- When view is loaded in a plain iframe
	def handle_no_permission(self):
		messages.error (self.request, "No tienes permiso para crear documentos.")
		target_url = reverse ("message-view")
		# Break out of the iframe and redirect the top window
		html = f""" <script> window.top.location.href = "{target_url}"; </script> """
		return HttpResponse(html)

	#-- Check uf user can create docs
	def userCanCreateDocs (self, request):
		user = request.user
		return any ([user.pais in x for x in ["COLOMBIA", "ECUADOR", "PERU"]])
