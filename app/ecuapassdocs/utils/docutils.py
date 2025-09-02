"""
Different general functions used in EcuapassDocs app 
"""

import os, json, tempfile

from ecuapassdocs.info.ecuapass_utils import Utils

class DocUtils:
	#-- Return pair key:params ['value'] from keys in paramsFields
	def getFieldsFromParams (paramsFields):
		fields = {}
		for key in paramsFields:
			fields [key] = paramsFields [key]['value']

		return fields

	#-- Return all doc form fiels: id, nro, pais, txt*, ref, date
	def getInputFieldsFromRequest (request):
		formFields = {}
		if request.POST:
			requestValues = request.POST 
			print (f"\n+++ {requestValues=}'")

			formFields ["id"]     = requestValues ["id"]
			formFields ["numero"] = requestValues ["numero"]
			formFields ["pais"]   = requestValues ["pais"]

			for key in [x for x in requestValues if x.startswith ("txt")]:
				formFields [key] = requestValues [key].replace ("\r\n", "\n")

			formFields ["fecha_creacion"]  = requestValues ["fecha_creacion"]
			formFields ["referencia"]      = requestValues ["referencia"]

		return formFields

	#-- Return all doc form fiels: id, nro, pais, txt*, ref, date
	def getFormFieldsFromRequest (request):
		formFields = {}

		requestValues = request.POST 

#		formFields ["id"]     = requestValues ["id"]
#		formFields ["numero"] = requestValues ["numero"]
#		formFields ["pais"]   = requestValues ["pais"]

		for key in [x for x in requestValues if x.startswith ("txt")]:
			formFields [key] = requestValues [key].replace ("\r\n", "\n")

#		formFields ["fecha_creacion"]  = requestValues ["fecha_creacion"]
#		formFields ["referencia"]      = requestValues ["referencia"]

		return formFields

	#-- Get values from DB into docParams
	@classmethod
	def getFormFieldsFromDB (cls, docType, pk):
		FormModel, DocModel = cls.getFormAndDocClass (docType)
		formInstance        = FormModel.objects.get (pk=pk)
		docInstance         = DocModel.objects.get (pk=pk)

		# Align text in fields with newlines 
		formFields = {}

		formFields ["id"]     = docInstance.id
		formFields ["numero"] = docInstance.numero
		formFields ["pais"]   = docInstance.pais

		for field in formInstance._meta.fields:	# Not include "numero" and "id"
			text     = getattr (formInstance, field.name)
			formFields [field.name] = text

		formFields ["fecha_creacion"]  = docInstance.fecha_creacion.isoformat()
		formFields ["referencia"]      = docInstance.referencia

		return formFields

	#-- Get doc fields from form fields (eg. txt01 --> 01_Transportista) 
	def getDocFieldsFromInputFields (docType, formFields):
		docFields   = {}
		paramFields = Utils.getInputsParameters (docType)

		for key, value in formFields.items ():
			docField  = paramFields [key]["ecudocsField"]
			docFields [docField] = value
		
		docFields = Utils.convertJsonFieldsNewlinesToWin (docFields)
		return docFields

	
	#-- Create temporal JSON file from fields dic
	def createTemporalJson (fields, prefix):
		tmpPath        = tempfile.gettempdir ()
		jsonFieldsPath = os.path.join (tmpPath, f"MANIFIESTO-{prefix}.json")
		json.dump (fields, open (jsonFieldsPath, "w"))
		return (jsonFieldsPath, tmpPath)

	def removeEmptyLinesFromText (text):
		lines = []
		for t in text.split ("\n"):
			if t.strip():
				lines.append (t.strip ())
		newText = "\n".join (lines)
		return newText

	def removeSpanishAccents (text):
		replacements = {
			'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u',
			'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U', 'Ü': 'U'
		}
		for accented, unaccented in replacements.items():
			text = text.replace(accented, unaccented)
		return text	

	#-------------------------------------------------------------------
	#-- Return form document class and register class from document type
	#-------------------------------------------------------------------
	def getFormAndDocClass  (docType):
		import app_cartaporte, app_manifiesto, app_declaracion

		FormModel, DocModel = None, None
		if docType.upper () == "CARTAPORTE":
			FormModel, DocModel = app_cartaporte.models_doccpi.CartaporteForm, app_cartaporte.models_doccpi.Cartaporte
		elif docType.upper () == "MANIFIESTO":
			FormModel, DocModel = app_manifiesto.models_docmci.ManifiestoForm, app_manifiesto.models_docmci.Manifiesto
		elif docType.upper () == "DECLARACION":
			FormModel, DocModel = app_declaracion.models_docdti.DeclaracionForm, app_declaracion.models_docdti.Declaracion 
		else:
			print  (f"Error: Tipo de documento '{docType}' no soportado")
			sys.exit  (0)

		return FormModel, DocModel


