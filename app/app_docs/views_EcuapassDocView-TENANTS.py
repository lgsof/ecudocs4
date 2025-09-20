# app_docs/views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import resolve, reverse
from django.utils.timezone import now
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from core.mixins import TenantRequiredMixin, require_tenant
# from core.tenant_context import get_current_empresa  # not needed here, mixin handles it

#--------------------------------------------------------------------
#-- FBV wrapper that renders the outer template (iframe host)
#--------------------------------------------------------------------
@require_tenant
def docView(request, *args, **kwargs):
	docType = request.path.strip('/').split('/')[0]
	if "pk" in kwargs:
		context = {"requestType": f"{docType}-editar", "pk": kwargs["pk"]}
	else:
		context = {"requestType": f"{docType}-nuevo"}
	return render(request, 'documento_forma_main.html', context)

#--------------------------------------------------------------------
#-- Main controller for new/edit/pdf/clone of a document
#--------------------------------------------------------------------
LAST_SAVED_VALUES = None

class EcuapassDocView(TenantRequiredMixin, LoginRequiredMixin, View):
	raise_exception = True
	permission_required = "app_cartaporte.add_cartaporte"

	def __init__(self, docType, background_image, parameters_file, *args, **kwargs):
		print(f"\n+++ Creando nueva vista EcuapassDocView...")
		super().__init__(*args, **kwargs)
		self.docType		  = docType
		self.template_name	  = "documento_forma_frame.html"
		self.background_image = background_image
		self.parameters_file  = parameters_file
		self.doc			  = DocEcuapass(self.docType, self.parameters_file)
		self.formFields		  = None
		# NOTE: current tenant available as self.empresa (set by TenantRequiredMixin.dispatch)

	#-------------------------------------------------------------------
	# Guard + permission check before GET/POST
	#-------------------------------------------------------------------
	def dispatch(self, request, *args, **kwargs):
		# TenantRequiredMixin already ensured tenant and set self.empresa
		if not self.userCanCreateDocs(request):
			return self.handle_no_permission()
		return super().dispatch(request, *args, **kwargs)

	#-------------------------------------------------------------------
	# GET: render the frame with the proper form fields/state
	#-------------------------------------------------------------------
	def get(self, request, *args, **kwargs):
		print("\n\n+++ GET :: EcuapassDocView +++")
		print(f"\t+++ getResponseForCommand::{request.GET=}'")
		urlCommand = resolve(request.path_info).url_name
		return self.getResponseForCommand(urlCommand, request, *args, **kwargs)

	#-------------------------------------------------------------------
	# POST: route by the button command
	#-------------------------------------------------------------------
	@method_decorator(csrf_protect)
	def post(self, request, *args, **kwargs):
		print("\n\n+++ POST :: EcuapassDocView +++")
		print(f"\t+++ getResponseForCommand::{request.POST=}'")
		buttonCommand = request.POST.get('boton_seleccionado', '').lower()
		return self.getResponseForCommand(buttonCommand, request, *args, **kwargs)

	#-------------------------------------------------------------------
	# Router for commands (nuevo/editar/guardar/pdf/clonar)
	#-------------------------------------------------------------------
	def getResponseForCommand(self, command, request, *args, **kwargs):
		# IMPORTANT: ensure all doc.* ORM calls use tenant-scoped managers
		self.formFields = self.doc.update(request, args, kwargs)

		if "nuevo" in command:
			return self.onEditCommand("NUEVO", request, *args, **kwargs)
		elif "editar" in command:
			return self.onEditCommand("BDATOS", request, *args, **kwargs)
		elif "guardar" in command:
			docId = self.onSaveCommand(request, args, kwargs)
			return HttpResponseRedirect(self.get_edit_url(docId))
		elif "pdf" in command:
			return self.onPdfCommand(command, request, *args, **kwargs)
		elif "clonar" in command:
			return self.onCloneCommand(command, request, *args, **kwargs)
		else:
			messages.add_message(request, messages.ERROR, f"ERROR: Opción '{command}' no existe")
			return render(request, 'messages.html')

	#-------------------------------------------------------------------
	# Edit: new / from DB / clone
	#-------------------------------------------------------------------
	def onEditCommand(self, editType, request, *args, **kwargs):
		print(f"\n+++ onEditCommand...")
		pk = kwargs.get('pk')

		if editType == "NUEVO":
			formFields = self.editDocumentNew(request)
		elif editType == "BDATOS":
			formFields = self.editDocumentFromDB(request, pk)
		elif editType == "CLON":
			formFields = self.editDocumentClon(request)

		# reflect input field constraints
		self.doc.updateFromFormFields(formFields)
		docParams = self.doc.getDocParamsFromFormFields(self.formFields)
		contextDic = {
			"docTitle": self.doc.getDocTitulo(),
			"docType": self.docType,
			"pais": self.doc.getDocPais(),
			"input_parameters": docParams,
			"background_image": self.background_image,
			"document_url": self.docType.lower(),
			"timestamp": now().timestamp()
		}
		return render(request, self.template_name, contextDic)

	def editDocumentNew(self, request):
		print(f"\n+++ Editing new document...'")
		formFields = self.doc.getFormFieldsFromRequest(request)
		formFields["id"] = ""
		formFields["numero"] = self.doc.generateDocNumberTemporal()
		formFields = self.doc.updateFromFormFields(formFields)
		self.formFields = formFields
		return self.formFields

	def editDocumentFromDB(self, request, pk):
		print(f"\n+++ Editing existing document {pk=}'")
		self.formFields = self.doc.getExistingDocumentFromDB(pk)
		return self.formFields

	def editDocumentClon(self, request):
		print(f"\n+++ Editing cloned document...'")
		self.formFields = self.doc.getFormFieldsFromRequest(request)
		self.formFields["numero"] = "CLON"
		self.formFields["txt00"] = "CLON"
		return self.formFields

	def onCloneCommand(self, command, request, *args, **kwargs):
		print(f"\n+++ onCloneCommand...")
		return self.onEditCommand("CLON", request, args, kwargs)

	#-------------------------------------------------------------------
	# PDF creation (reads from DB or request)
	#-------------------------------------------------------------------
	def onPdfCommand(self, pdfType, request, *args, **kwargs):
		print(f"\n+++ onPdfCommand:", request.method, ": PK :", kwargs.get("pk"))
		if request.method == "GET":
			pk = int(request.GET.get("pk"))
			pdfType = request.GET.get("pdfType")
			self.formFields = self.doc.getFormFieldsFromDB(pk)
		else:
			self.formFields = self.doc.getFormFieldsFromRequest(request)

		docPdfCreator = DocPdfCreator(self.docType)
		return docPdfCreator.createPdf(pdfType, self.formFields)

	#-------------------------------------------------------------------
	# Save (new/existing). MT NOTE: rely on tenant-scoped managers inside DocEcuapass
	#-------------------------------------------------------------------
	def onSaveCommand(self, request, *args, **kwargs):
		print("+++ onSaveCommand...")
		pk = kwargs.get('pk')
		docNumber = self.formFields["numero"]
		if "NUEVO" in docNumber or "CLON" in docNumber:
			docId = self.doc.saveDocumentNewToDB()
		else:
			docId = self.doc.saveDocumentExistingToDB()
		return docId

	# (your change-tracking helpers left as-is)

	#----------------------------------------------------------------
	# URL helper
	#----------------------------------------------------------------
	def get_edit_url(self, pk: int) -> str:
		url_name = f"{self.docType.lower()}-editardoc"
		return reverse(url_name, kwargs={"pk": pk})

	#----------------------------------------------------------------
	# Permission helpers
	#----------------------------------------------------------------
	def handle_no_permission(self):
		messages.error(self.request, "No tienes permiso para crear documentos.")
		target_url = reverse("message-view")
		html = f"""<script> window.top.location.href = "{target_url}"; </script>"""
		return HttpResponse(html)

	def userCanCreateDocs(self, request):
		user = request.user
		return any([user.pais in x for x in ["COLOMBIA", "ECUADOR", "PERU"]])

