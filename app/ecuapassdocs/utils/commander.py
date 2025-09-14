
from django.http import HttpResponse

from ecuapassdocs.info.ecuapass_utils import Utils
from ecuapassdocs.utils.models_scripts import Scripts
from ecuapassdocs.utils.docutils import DocUtils
from ecuapassdocs.utils.pdfcreator import CreadorPDF

from urllib.parse import quote

import app_cartaporte
import app_manifiesto

class Commander:
	def __init__ (self, docType):
		self.docType = docType

	#-------------------------------------------------------------------
	#-------------------------------------------------------------------
	def createPdf (self, pdfCommand, formFields):
		# Create a single PDF or PDF with child documents (Cartaporte + Manifiestos)
		if "paquete" in pdfCommand:
			pdfResponse = self.createPdfResponseMultiDoc (formFields)
		else:
			pdfResponse = self.createPdfResponseSingleDoc (formFields, pdfCommand)
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

			outPdfPath = creadorPDF.createPdfFileMultiDoc (inputValuesList, docTypesList)
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
			outPdfPath = creadorPDF.createPdfFileSingleDoc (self.docType, formFields, pdfType)
			return self.createPdfResponse (outPdfPath)
		except Exception as ex:
			Utils.printException ("Error creando PDF simple")
		return None

	#-- Create PDF response
	def createPdfResponse(self, outPdfPath):
		import os
		from django.http import HttpResponse
		
		filename = os.path.basename(outPdfPath)
	
		with open(outPdfPath, 'rb') as pdf_file:
			response = HttpResponse(pdf_file.read(), content_type='application/pdf')
			response['Content-Disposition'] = f'inline; filename="{filename}"'
			
			# Cache control headers
			response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
			response['Pragma'] = 'no-cache'
			response['Expires'] = '0'
			
		return response


