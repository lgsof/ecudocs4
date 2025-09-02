#!/usr/bin/env python3

import os, sys, json, re, time
import PyPDF2

from pickle import load as pickle_load
import asyncio  # For calling Azure asynchronous functions (EcuFeedback)

from ecuapassdocs.info.ecuapass_info_cartaporte_NTA import CartaporteNTA
from ecuapassdocs.info.ecuapass_info_BYZA import Cartaporte_BYZA
from ecuapassdocs.info.ecuapass_info_cartaporte_LOGITRANS import CartaporteLogitrans
from ecuapassdocs.info.ecuapass_info_manifiesto_NTA import ManifiestoNTA
from ecuapassdocs.info.ecuapass_info_BYZA import Manifiesto_BYZA
from ecuapassdocs.info.ecuapass_info_manifiesto_LOGITRANS import ManifiestoLogitrans
from ecuapassdocs.info.ecuapass_utils import Utils

from ecuapass_azure import EcuAzure
from ecuapass_feedback import EcuFeedback
from ecuapass_settings import EcuSettings
from bot_codebin import  CodebinBot
from ecuapass_exceptions import *

USAGE="\n\
Extract info from ECUAPASS documents in PDF (cartaporte|manifiesto|declaracion).\n\
USAGE: ecuapass_doc.py <PDF document>\n"

def main ():
	if (len (sys.argv) < 2):
		print (USAGE)
	else:
		docFilepath = sys.argv [1]

		# For DEBUG: Check if exists a previous downloaded EcuFields document
		ecuFilepath = docFilepath.replace (".pdf", "-ECUFIELDS.json")
		if os.path.exists (ecuFilepath):
			BotScraping.webdriver = None
		else:
			CodebinBot.loadWebdriver ()

		#ecuDoc = EcuDoc ()
		#ecuDoc.extractDocumentFields (docFilepath, os.getcwd())
		runningDir = os.getcwd()
		EcuDoc.analyzeDocument (docFilepath, runningDir, CodebinBot.webdriver)

#-----------------------------------------------------------
# Run cloud analysis
#-----------------------------------------------------------
class EcuDoc:
	#----------------------------------------------------------------
	#-- Analyze one document given its path
	# Extract fields info from PDF document (using CODEBIN bot)
	#----------------------------------------------------------------
	def analyzeDocument (docFilepath, runningDir):
		try:
			# Check if PDF is a valid ECUAPASS document")
			EcuDoc.checkIsValidDocument (docFilepath)

			# Change to workingdir
			path       = os.path.dirname (docFilepath)
			workingDir = path if path else os.getcwd()
			os.chdir (workingDir)

			# Load "empresa": reads and checks if "settings.txt" file exists')
			ecuSettings    = EcuSettings (runningDir)
			credentials    = ecuSettings.readBinSettings ()
			empresa        = credentials ["empresa"]

			# Start document processing"
			filename          = os.path.basename (docFilepath)
			docType           = Utils.getDocumentTypeFromFilename (filename)
			docFieldsFilename = EcuDoc.getDocFieldsFromCodebin (docFilepath, docType, credentials)

			# Send file as feedback
			try:
				feedback = EcuFeedback (credentials ["azrConnString"])
				asyncio.run (feedback.sendLog (empresa, docFilepath))
			except Exception as ex:
				Utils.printx (f"EXCEPCION: enviando feedback: '{ex}'")

			# Get document Fields and save to other formats (ecuFields, cbinFields)
			infoDoc   = EcuDoc.createInfoDocument (empresa, docType, docFieldsFilename, runningDir)
			ecuFile   = EcuDoc.saveFields (infoDoc.extractEcuapassFields (), filename, "ECUFIELDS")
			docFile   = EcuDoc.saveFields (infoDoc.getDocFields (),   filename, "DOCFIELDS")
			cbinFile  = EcuDoc.saveFields (infoDoc.getCodebinFields(),  filename, "CBINFIELDS")

			return (Utils.printx (f"EXITO: Documento procesado: '{docFilepath}'"))
		except EcudocDocumentNotFoundException as ex:
			return (Utils.printx (f"ERROR: Documento no encontrado:\\\\{str(ex)}"))
		except EcudocConnectionNotOpenException as ex:
			return (Utils.printx (f"ERROR: Problemas conectandose al CODEBIN: {str(ex)}"))
		except Exception as ex:
			Utils.printException (ex)
			return (Utils.printx (f"ERROR: No se pudo extraer campos del documento:\\\\{str(ex)}"))

	#------------------------------------------------------
	#-- Get document fields from PDF document
	#------------------------------------------------------
	def getDocFieldsFromCodebin (docFilepath, docType, credentials):
		# CACHE: Check codebin .json cache document
		docFieldsFilename = EcuDoc.loadCodebinCache (docFilepath)
		if docFieldsFilename:
			return docFieldsFilename

		webdriver = CodebinBot.loadWebdriver ()
		# CODEBIN BOT: Get data from CODEBIN web
		Utils.printx (f">>>>>>>>>>>>>>>>> Buscando documento '{docFilepath}' en CODEBIN <<<<<<<<<<<<<<<<<<<<<<<")
		filename          = os.path.basename (docFilepath)
		codebinBot        = CodebinBot (docFilepath, credentials, webdriver)
		docFieldsFilename = codebinBot.downloadDocument ()
		Utils.printx (">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
		return docFieldsFilename
		
	#----------------------------------------------------------------
	#-- Load previous result
	#----------------------------------------------------------------
	def loadCodebinCache (docFilepath):
		fieldsJsonFile = None
		try:
			#filename       = os.path.basename (docFilepath)
			filename       = docFilepath
			cacheFilename = f"{filename.split ('.')[0]}-CBINFIELDS.json"
			Utils.printx (f"Buscando archivo CODEBIN cache '{cacheFilename}'...")
			if os.path.exists (cacheFilename): 
				Utils.printx ("...Archivo encontrado.")
				with open (cacheFilename, 'r') as inFile:
					codebinValues = json.load (inFile)
				docType        = Utils.getDocumentTypeFromFilename (docFilepath)
				docNumber      = Utils.getDocumentNumberFromFilename (docFilepath)
				azureValues    = Utils.getAzureValuesFromCodebinValues (docType, codebinValues, docNumber)
				fieldsJsonFile = Utils.saveFields (azureValues, docFilepath, "DOCFIELDS")
		except:
			Utils.printException (f"Cargando documento desde cache: '{filename}'")
			raise

		return (fieldsJsonFile)

	def loadAzureCache (docFilepath):
		fieldsJsonFile = None
		try:
			#filename       = os.path.basename (docFilepath)
			filename       = docFilepath
			pickleFilename = f"{filename.split ('.')[0]}-CACHE.pkl"
			Utils.printx (f"Buscando archivo cache '{pickleFilename}'...")
			if os.path.exists (pickleFilename): 
				Utils.printx ("...Archivo encontrado.")
				with open (pickleFilename, 'rb') as inFile:
					result = pickle_load (inFile)
				fieldsJsonFile = EcuAzure.saveResults (result, filename)
			else:
				Utils.printx (f"...Archivo cache no existe'")
		except:
			Utils.printx (f"EXCEPCION: cargando documento desde cache: '{filename}'")
			Utils.printException ()
			#raise

		return (fieldsJsonFile)
	
	#----------------------------------------------------------------
	#-- Get embedded fields info from PDF
	#----------------------------------------------------------------
	def getEmbeddedFieldsFromPDF (pdfPath):
		fieldsJsonPath = pdfPath.replace (".pdf", "-FIELDS.json")
		try:
			with open(pdfPath, 'rb') as pdf_file:
				pdf_reader = PyPDF2.PdfReader(pdf_file)

				# Assuming the hidden form field is added to the first page
				first_page = pdf_reader.pages[0]

				# Extract the hidden form field value 
				text     = first_page.extract_text()  
				jsonText = re.search ("Embedded_jsonData: ({.*})", text).group(1)
				Utils.printx ("Obteniendo campos desde el archivo PDF...")
				fieldsJsonDic  = json.loads (jsonText)
				json.dump (fieldsJsonDic, open (fieldsJsonPath, "w"), indent=4, sort_keys=True)
		except Exception as e:
			Utils.printx ("EXCEPCION: Leyendo campos embebidos en el documento PDF.")
			return None

		return (fieldsJsonPath)


	#-- Save fields dict in JSON 
	def saveFields (fieldsDict, filename, suffixName, sort=False):
		prefixName	= filename.split(".")[0]
		outFilename = f"{prefixName}-{suffixName}.json"
		fp = open (outFilename, "w") 
		json.dump (fieldsDict, fp, indent=4)
		fp.close ()
		#with open (outFilename, "w") as fp:
		#	json.dump (fieldsDict, fp, indent=4, default=str, sort_keys=False)

		return outFilename

	#-----------------------------------------------------------
	# Return document class for document type and empresa
	#-----------------------------------------------------------
	def createInfoDocument (empresa, docType, docFieldsFilename, runningDir):
		infoDoc = None
		if docType.upper() == "CARTAPORTE":
			if "BYZA" in empresa:
				infoDoc  = Cartaporte_BYZA (docFieldsFilename, runningDir)
			elif "NTA" in empresa:
				infoDoc  = CartaporteNTA (docFieldsFilename, runningDir)
			elif "LOGITRANS" in empresa:
				infoDoc  = CartaporteLogitrans (docFieldsFilename, runningDir)
			else:
				raise Exception (f"Empresa '{empresa}' no registrada")
		elif docType.upper() == "MANIFIESTO":
			if "BYZA" in empresa:
				infoDoc = Manifiesto_BYZA (docFieldsFilename, runningDir)
			elif "NTA" in empresa:
				infoDoc = ManifiestoNTA (docFieldsFilename, runningDir)
			elif "LOGITRANS" in empresa:
				infoDoc = ManifiestoLogitrans (docFieldsFilename, runningDir)
			else:
				raise Exception (f"Empresa '{empresa}' no registrada")
		elif docType.upper() == "DECLARACION":
			Utils.printx (f"ALERTA: '{docType}' no están soportadas")
			raise Exception (f"Tipo de documento '{docType}' desconocido")

		return infoDoc

	#----------------------------------------------------------------
	#-- Check if document filename is an image (.png) or a PDF file (.pdf)
	#----------------------------------------------------------------
	def checkIsValidDocument (filepath):
		filename  = os.path.basename (filepath)
		extension = filename.split (".")[1]
		if extension.lower() not in ["PDF", "pdf"]:
			raise EcudocDocumentNotValidException (f"Tipo de documento '{docFilepath}' no válido")
		return True

#--------------------------------------------------------------------
# Call main 
#--------------------------------------------------------------------
if __name__ == '__main__':
	main ()
