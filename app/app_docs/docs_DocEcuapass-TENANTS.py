"""
General class for handling documents for cartaporte, manifiesto, declaracion
Tenant-safe version
"""

import uuid
from django.urls import resolve
from django.db import transaction

from ecuapassdocs.utils.resourceloader import ResourceLoader 
from ecuapassdocs.info.ecuapass_utils import Utils

from app_cartaporte.models_doccpi import Cartaporte
from app_manifiesto.models_docmci import Manifiesto, ManifiestoForm
from app_declaracion.models_docdti import Declaracion, DeclaracionForm
from ecuapassdocs.utils.models_scripts import Scripts


class DocEcuapass:
	def __init__ (self, docType, paramsFile):
		print (f"\n+++ Creando nuevo DocEcuapass...")
		self.docType	 = docType
		self.inputParams = ResourceLoader.loadJson ("docs", paramsFile)
		self.ModelCLASS  = self.getDocModelCLASS ()

		# formFields holds UI fields  (id, numero, usuario, empresa, pais, url, txtNN)
		self.formFields  = {k: "" for k in self.inputParams.keys ()}

		# MT: cache current tenant  (Empresa instance) and country once update () runs
		self.empresa = None  # MT: Empresa instance  (FK target)
		self.pais	 = None

	#-------------------------------------------------------------------
	# Print all instance variables
	#-------------------------------------------------------------------
	def printInfo (self):
		print (f"\n+++ Info current doc:'")
		for key, value in vars (self).items ():

			print (f"\n\t{key}: {value}")

	#-------------------------------------------------------------------
	# Update from view form fields  (called on every request)
	#-------------------------------------------------------------------
	def update (self, request, args, kwargs):
		# MT: use Empresa instance directly; keep a human value in formFields if you need to show it
		self.id		  = kwargs.get ("pk", "")    # pk or "" if pk doesn't exist
		self.numero   = ""
		self.usuario  = request.user.username
		self.empresa  = getattr (request, "empresa", None)  # MT: Empresa object
		self.pais	  = request.session.get ("pais")
		self.url	  = resolve (request.path_info).url_name

		if not self.empresa:
			raise RuntimeError ("Tenant  (empresa) missing in request")

		# Fill formFields
		formFields = self.createFormFields ()
		# Keep a readable string for UI; underlying save will use Empresa FK from self.empresa
		# If you prefer a different label, adjust here  (e.g., nombre instead of nickname)
		if hasattr (self.empresa, "nickname"):
			formFields["empresa"] = self.empresa.nickname
		else:
			formFields["empresa"] = getattr (self.empresa, "nombre", str (self.empresa.pk))

		formFields["usuario"] = self.usuario
		formFields["pais"]	  = self.pais
		formFields["url"]	  = self.url

		if request.POST:
			requestFields = request.POST
			self.id		  = requestFields.get ("id", "") or ""
			self.numero   = requestFields.get ("numero", "") or ""
			for f in ["id", "numero", "usuario", "empresa", "pais", "url"]:
				if f in requestFields:
					formFields[f] = requestFields[f]
			for key in [x for x in requestFields.keys () if x.startswith ("txt")]:
				formFields[key] = requestFields[key].replace ("\r\n", "\n")

		self.formFields = formFields
		return self.formFields

	#-- Update from formFields
	def updateFromFormFields (self, formFields):
		for key in ["id", "numero", "usuario", "empresa", "pais", "url"]:
			if key in formFields:
				setattr (self, key, formFields[key])
		self.formFields = formFields
		return self.formFields

	#----------------------------------------------------------------
	def getFormFields (self):
		return self.formFields

	def getTxtFields (self):
		return {k: v for k, v in self.formFields.items () if k.startswith ("txt")}

	#-------------------------------------------------------------------
	# Save new or existing doc to DB  (router)
	#-------------------------------------------------------------------
	def saveDocumentToDB (self):
		if "NUEVO" in  (self.numero or ""):
			return self.saveDocumentNewToDB ()
		elif "CLON" in  (self.numero or ""):
			# You could route to a dedicated clone flow if needed
			return self.saveDocumentNewToDB ()
		else:
			return self.saveDocumentExistingToDB ()

	#-- Save new document ----------------------------------------------
	@transaction.atomic
	def saveDocumentNewToDB (self):
		print (f">>> Guardando '{self.docType}' nuevo en la BD...")

		# MT: generate the final doc number under a lock to reduce race risk
		self.numero = self.generateDocNumberFinal ()

		# Create doc instance and assign empresa explicitly  (belt & suspenders)
		docInstance = self.ModelCLASS ()
		if hasattr (docInstance, "empresa_id") and self.empresa:
			docInstance.empresa = self.empresa	# MT: explicit tenant FK

		# Expect your model's .update (doc=self) to copy fields  (incl. numero, pais, documento)
		docInstance.update (doc=self)
		return docInstance.id

	#-- Save existing document -----------------------------------------
	@transaction.atomic
	def saveDocumentExistingToDB (self):
		print (f"+++\t Guardando '{self.docType}' existente en la BD...")

		# MT: rely on tenant-scoped manager to avoid cross-tenant pk access
		docInstance = self.ModelCLASS.objects.filter (id=self.id).first ()
		if not docInstance:
			raise ValueError (f"Documento id={self.id} no encontrado para este tenant")

		# Ensure tenant cannot be switched inadvertently
		if hasattr (docInstance, "empresa_id") and self.empresa:
			docInstance.empresa = self.empresa	# keep consistent

		docInstance.update (doc=self)

		# Optional: handle "SUGERIDO" doc number case if you still use it
		if self.numero == "SUGERIDO":
			# NOTE: Using self.ModelCLASS for numbering keeps things consistent
			new_number = Utils.getCodigoPaisFromPais (self.pais) + "00001"
			self.numero = new_number
			if hasattr (docInstance, "numero"):
				docInstance.numero = new_number
			# If there's a related "documento" form model mirroring numero:
			if hasattr (docInstance, "documento") and docInstance.documento:
				docInstance.documento.numero = new_number
				docInstance.documento.save ()
			docInstance.save ()

		return docInstance.id

	#-------------------------------------------------------------------
	#-- Return form document class and register class from document type
	#-------------------------------------------------------------------
	def getDocModelCLASS (self):
		import app_cartaporte, app_manifiesto, app_declaracion
		if self.docType == "CARTAPORTE":
			return app_cartaporte.models_doccpi.Cartaporte
		elif self.docType == "MANIFIESTO":
			return app_manifiesto.models_docmci.Manifiesto
		elif self.docType == "DECLARACION":
			return app_declaracion.models_docdti.Declaracion
		else:
			raise Exception (f"Error: Tipo de documento '{self.docType}' no soportado")

	#-------------------------------------------------------------------
	#-- Generate doc number from last doc number saved in DB
	#-------------------------------------------------------------------
	def generateDocNumberTemporal (self):
		docType = Utils.getDocPrefix (self.docType)
		return f"NUEVO-{docType}-{str (uuid.uuid4 ())}"

	@transaction.atomic
	def generateDocNumberFinal (self):
		"""
		MT-safe-ish: uses tenant-scoped manager  (empresa) and filters by pais.
		For strict guarantees under concurrency, consider select_for_update ()
		on a sequence/row that tracks the last number per  (empresa, pais, docType).
		"""
		docType   = Utils.getDocPrefix (self.docType)
		num_zeros = 5

		# MT: manager is tenant-scoped; add pais filter as in your original code
		lastDoc =  (
			self.ModelCLASS.objects
			.filter (pais=self.pais)
			.exclude (numero="SUGERIDO")
			.order_by ("-id")
			.first ()
		)
		if lastDoc:
			lastNumber = Utils.getNumberFromDocNumber (lastDoc.numero)
			newNumber  = str (lastNumber + 1).zfill (num_zeros)
		else:
			newNumber  = str (1).zfill (num_zeros)

		docNumber = Utils.getCodigoPaisFromPais (self.pais) + newNumber
		return docNumber

	#-------------------------------------------------------------------
	# Titles / simple getters
	#-------------------------------------------------------------------
	def getDocNumero (self):
		return self.numero or ""

	def getDocTitulo (self):
		return Utils.getDocPrefix (self.docType) + " : " + self.getDocNumero ()

	def getDocPais (self):
		return self.pais

	#-------------------------------------------------------------------
	# Fetch existing doc  (tenant-scoped)
	#-------------------------------------------------------------------
	def getExistingDocumentFromDB (self, idRecord):
		record = self.ModelCLASS.objects.filter (id=idRecord).first ()  # MT: tenant-scoped
		if not record:
			raise ValueError (f"Documento id={idRecord} no encontrado para este tenant")
		docParams  = record.getDocParams (self.inputParams)
		formFields = self.getFormFieldsFromDocParams (docParams)
		return formFields

	#----------------------------------------------------------------
	# Getters/Setters/Converters between fields  (formFields, docParams)
	#----------------------------------------------------------------
	def createFormFields (self):
		"""
		Initialize default form fields based on docType and tenant.
		"""
		formFields = self.getFormFieldsFromDocParams (self.inputParams)

		# MT: you already have the Empresa instance → no need to look it up by nickname
		if self.docType == "MANIFIESTO" and self.empresa is not None:
			# Example: pull empresa.permiso if your Empresa model has it
			permiso = getattr (self.empresa, "permiso", None)
			if permiso:
				formFields["txt02"] = permiso

		self.formFields = formFields
		return self.formFields

	def getFormFieldsFromDocParams (self, docParams):
		return {k: v["value"] for k, v in docParams.items ()}

	def getFormFieldsFromDB (self, idRecord):
		record = self.ModelCLASS.objects.filter (id=idRecord).first ()  # MT: tenant-scoped
		if not record:
			raise ValueError (f"Documento id={idRecord} no encontrado para este tenant")
		docParams  = record.getDocParams (self.inputParams)
		self.formFields = self.getFormFieldsFromDocParams (docParams)
		return self.formFields

	def getFormFieldsFromRequest (self, request):
		print (f"\n+++ ...getFormFieldsFromRequest...")
		formFields = {}

		formFields["usuario"] = request.user.username
		# Keep a display string for empresa; the FK is handled via self.empresa
		empresa_display = getattr (getattr (request, "empresa", None), "nickname", None)
		if not empresa_display:
			empresa_display = getattr (getattr (request, "empresa", None), "nombre", "")
		formFields["empresa"] = empresa_display or ""
		formFields["pais"]	  = request.session.get ("pais")
		formFields["url"]	  = resolve (request.path_info).url_name

		if request.POST:
			formFields["id"]	 = request.POST.get ("id")
			formFields["numero"] = request.POST.get ("numero")
			for key in [x for x in request.POST if x.startswith ("txt")]:
				formFields[key] = request.POST[key].replace ("\r\n", "\n")

		self.formFields = formFields
		return self.formFields

	def getDocParamsFromFormFields (self, formFields):
		docParams = self.inputParams
		for k in formFields.keys ():
			if k in docParams:
				docParams[k]["value"] = formFields[k]
		self.docParams = docParams
		return self.docParams

	#-------------------------------------------------------------------
	# Save suggested manifiesto  (tenant-safe)
	#-------------------------------------------------------------------
	def saveSuggestedManifiesto (self, cartaporteDoc, docFields):
		print ("+++ Guardando manifiesto sugerido en la BD...")
		print ("+++ Pais:", self.pais, ". Usuario:", self.usuario)
		if not self.empresa:
			raise RuntimeError ("Tenant  (empresa) missing for saveSuggestedManifiesto")

		# First: save DocModel
		docModel = Manifiesto (pais=self.pais, usuario=self.usuario)
		# MT: set empresa explicitly
		if hasattr (docModel, "empresa_id"):
			docModel.empresa = self.empresa
		docModel.numero = "SUGERIDO"
		docModel.save ()

		# Second, save FormModel
		formModel = ManifiestoForm (id=docModel.id, numero=docModel.numero)
		docFields["txt00"] = formModel.numero

		# Third, set FormModel values from input form values
		for key, value in docFields.items ():
			if key not in ["id", "numero"]:
				setattr (formModel, key, value)

		# Fourth, save FormModel and update DocModel with FormModel
		formModel.save ()
		docModel.documento	= formModel
		docModel.cartaporte = cartaporteDoc
		docModel.save ()
		return docModel

