
from django.http import HttpResponse

from ecuapassdocs.info.ecuapass_utils import Utils
from ecuapassdocs.utils.models_scripts import Scripts
from .pdfcreator import CreadorPDF 
from ecuapassdocs.utils.docutils import DocUtils

import app_cartaporte
import app_manifiesto

class Commander:
	def __init__ (self, docType):
		self.docType = docType
	#-------------------------------------------------------------------
	#-------------------------------------------------------------------
	def onPdfCommand (self, pdfType, request, *args, **kwargs):
		print (f"\n+++ onPdfCommand:", request.method, ": PK :", kwargs.get ("pk"))
		if request.method == "GET":
			pk = kwargs.get ('pk')
			formFields = DocUtils.getFormFieldsFromDB (self.docType, pk)
		else:
			formFields = DocUtils.getFormFieldsFromRequest (request)

		# Create a single PDF or PDF with child documents (Cartaporte + Manifiestos)
		if "paquete" in pdfType:
			pdfResponse = self.createPdfResponseMultiDoc (formFields)
		else:
			pdfResponse = self.createPdfResponseSingleDoc (formFields, pdfType)
		return pdfResponse

	#-------------------------------------------------------------------
	# Create PDF for 'Cartaporte' plus its 'Manifiestos'
	#-------------------------------------------------------------------
	def createPdfResponseMultiDoc (self, docFields):
		try:
			print ("+++ Creando respuesta PDF múltiple...")
			creadorPDF = CreadorPDF ("MULTI_PDF")

			# Get docFields for Cartaporte childs
			id = docFields ["id"]
			valuesList, typesList = self.getInputValuesForDocumentChilds (self.docType, id)
			inputValuesList		  = [docFields] + valuesList
			docTypesList		  = [self.docType] + typesList

			outPdfPath = creadorPDF.createMultiPdf (inputValuesList, docTypesList)
			return self.createPdfResponse (outPdfPath)
		except Exception as ex:
			Utils.printException ("Error creando PDF múltiple")
		return None

	#-------------------------------------------------------------------
	# Create PDF for 'Cartaporte' plus its 'Manifiestos'
	#-------------------------------------------------------------------
	def getInputValuesForDocumentChilds (self, docType, docId):
		outInputValuesList = []
		outDocTypesList    = []
		try:
			regCartaporte	= app_cartaporte.models_doccpi.Cartaporte.objects.get (id=docId)
			regsManifiestos = app_manifiesto.models_docmci.Manifiesto.objects.filter (cartaporte=regCartaporte)

			for reg in regsManifiestos:
				docManifiesto  = app_manifiesto.models_docmci.ManifiestoForm.objects.get (id=reg.id)
				docFields = model_to_dict (docManifiesto)
				docFields ["txt41"] = "COPIA"

				outInputValuesList.append (docFields)
				outDocTypesList.append ("MANIFIESTO")
		except Exception as ex:
			Utils.printException ()
			#print (f"'No existe {docType}' con id '{id}'")

		return outInputValuesList, outDocTypesList

	#-------------------------------------------------------------------
	#-- Create a simple PDF 
	#-------------------------------------------------------------------
	def createPdfResponseSingleDoc (self, formFields, pdfType):
		try:
			print ("+++ Creando respuesta PDF simple...")
			creadorPDF = CreadorPDF ("ONE_PDF")
			outPdfPath = creadorPDF.createPdfDocument (self.docType, formFields, pdfType)
			return self.createPdfResponse (outPdfPath)
		except Exception as ex:
			Utils.printException ("Error creando PDF simple")
		return None

	#-- Create PDF response
	def createPdfResponse (self, outPdfPath):
		with open(outPdfPath, 'rb') as pdf_file:
			pdfContent = pdf_file.read()

		# Prepare and return HTTP response for PDF
		pdfResponse = HttpResponse (content_type='application/pdf')
		pdfResponse ['Content-Disposition'] = f'inline; filename="{outPdfPath}"'
		pdfResponse.write (pdfContent)

		return pdfResponse

