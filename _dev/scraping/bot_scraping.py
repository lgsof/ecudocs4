#!/usr/bin/env python3

"""
Fill CODEBIN web form from JSON fields document.
"""
import sys, json, re, time, os
import PyPDF2

from threading import Thread as threading_Thread

import selenium
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from ecuapassdocs.info.ecuapass_utils import Utils
from ecuapassdocs.info.resourceloader import ResourceLoader 
from ecuapassdocs.info.ecuapass_info_cartaporte import CartaporteInfo

from ecuapass_exceptions import EcudocDocumentNotFoundException, EcudocConnectionNotOpenException

#----------------------------------------------------------------
# Bot for filling CODEBIN forms from ECUDOCS fields info
#----------------------------------------------------------------
class BotScraping:
	def __init__ (self, pdfFilepath, credentials, webdriver):
		self.credentials = credentials
		self.empresa     = credentials ["empresa"]
		self.url         = credentials ["urlCodebin"]

		# Init bot settings
		self.docNumber             = Utils.getDocumentNumberFromFilename (pdfFilepath) # Special for NTA
		self.docType               = Utils.getDocumentTypeFromFilename (pdfFilepath)
		self.pais, self.codigoPais = Utils.getPaisCodigoFromDocNumber (self.docNumber)
		self.user, self.password   = self.getUserPasswordForPais (self.pais)

		self.webdriver             = BotScraping.webdriver

	#------------------------------------------------------
	# Load webdriver 
	# Static as it is called in background in analyze_docs
	#------------------------------------------------------
	@staticmethod
	def loadWebdriver ():
		Utils.printx ("Getting webdriver...")
		# Load the webdriver
		while not hasattr (BotScraping, "webdriver"):
			Utils.printx ("...Loading webdriver...")
			BotScraping.startWebdriver ()
			BotScraping.IS_OPEN = False
			BotScraping.LAST_PAIS = ""
			BotScraping.DOC_FOUND = False
			#BotScraping.webdriver = webdriver.Firefox ()
			Utils.printx ("...Webdriver Loaded")
		return BotScraping.webdriver

	#-- Start webdriver, with options, from browser driver
	def startWebdriver ():
		options = Options()
		options.add_argument("--headless")
		BotScraping.webdriver = webdriver.Firefox (options=options)

	#-------------------------------------------------------------------
	# Download doc file with doc fields (old azr fields)
	#-- Get the CODEBIN id from document number
	#-- List documents, search the number, and get the id of selected
	#------------------------------------------------------
	def downloadDocument (self):
		try:
			# Call to bot to get values from CODEBIN web
			urlSettings  = self.getCodebinUrlSettingsForEmpresa ()

			self.initWebdriver ()
			self.openCodebin ()
			self.loginCodebin (self.pais)
			self.locateSearchSite (urlSettings)
			docForm       = self.searchDocumentInSite (urlSettings, self.docNumber)
			codebinValues = self.getVauesFromForm (docForm, self.codigoPais, self.docNumber)

			outDocFilename = self.saveScrapedValues (codebinValues)

			self.closeInitialCodebinWindow ()
			return outDocFilename
		except EcudocDocumentNotFoundException:
			BotScraping.DOC_FOUND = False
			raise 
		except EcudocConnectionNotOpenException:
			self.quitCodebin ()
			raise
		except:
			#self.quitCodebin ()
			Utils.printException ()
			raise Exception ("No se pudo conectar a CODEBIN. Intentelo nuevamente.") 

		return None

	#------------------------------------------------------
	# Overriden methods implemented in child classes
	#------------------------------------------------------
	def openCodebin (self):
		print ("xxx openCodebin not implemented...")

	def loginCodebin (self, pais):
		print ("xxx loginCodebin not implemented...")

	def locateSearchSite (self):
		print ("xxx locateSearchSite not implemented...")
	
	def searchDocumentInSite (self, urlSettings, docNumber):
		print ("xxx searchDocumentInSite not implemented...")

	def getVauesFromForm (self, docForm, codigoPais, docNumber):
		print ("xxx getVauesFromForm not implemented...")

	#------------------------------------------------------
	# Save and convert scraped values
	#------------------------------------------------------
	def saveScrapedValues (self, codebinValues):
		# Format to Azure values
		azureValues = Utils.getAzureValuesFromCodebinValues (self.docType, codebinValues, self.docNumber)
		azureValues = Utils.convertJsonFieldsNewlinesToWin (azureValues)
		# Save data
		outCbinFilename = f"{self.docType}-{self.empresa}-{self.docNumber}-CBINFIELDS.json"
		outDocFilename  = f"{self.docType}-{self.empresa}-{self.docNumber}-DOCFIELDS.json"
		json.dump (codebinValues, open (outCbinFilename, "w"), indent=4)
		json.dump (azureValues, open (outDocFilename, "w"), indent=4, sort_keys=True)

		BotScraping.DOC_FOUND = True
		BotScraping.LAST_PAIS = self.pais
		BotScraping.IS_OPEN   = True

		return outDocFilename

	#------------------------------------------------------
	#------------------------------------------------------
	def getUserPasswordForPais (self, pais):
		user, password = None, None
		if pais.upper() == "COLOMBIA":
			user      = self.credentials ["userColombia"]
			password  = self.credentials ["passwordColombia"]
		elif pais.upper() == "ECUADOR":
			user      = self.credentials ["userEcuador"]
			password  = self.credentials ["passwordEcuador"]
		elif pais.upper() == "PERU":
			user      = self.credentials ["userPeru"]
			password  = self.credentials ["passwordPeru"]
		else:
			raise Exception (Utils.printx (f"No se asigno user/password. Pais no existente:", pais))

		return user, password


	#-------------------------------------------------------------------
	#-------------------------------------------------------------------
	def quitCodebin (self):
		#-- Webdriver is killed by the main function as it is an independent thread
		if BotScraping.webdriver:
			print ("+++ CODEBIN: ...Quitando driver")
			BotScraping.webdriver.quit ()

		Utils.printx ("+++ CODEBIN: ...Reiniciando variables")
		BotScraping.IS_OPEN   = False
		BotScraping.LAST_PAIS = ""
		BotScraping.DOC_FOUND = False
		BotScraping.webdriver = None
		self.webdriver       = None

	#-------------------------------------------------------------------
	# Initial browser opening
	# Open codebin session for new docs or go back to begina a new search
	#-------------------------------------------------------------------
	def initWebdriver (self):
		try:
			cb = BotScraping
			print (f"+++ CODEBIN...IS_OPEN: {cb.IS_OPEN}. LAST_PAIS: {cb.LAST_PAIS}, DOC_FOUND: {cb.DOC_FOUND}")
			print (f"+++ CODEBIN...WEBDRIVER: {BotScraping.webdriver}")

			if self.downloadingSameTypeDocs ():
				print ("+++ CODEBIN: ...Regresando...")
				self.webdriver.back ()    # Search results
			else:
				print ("+++ CODEBIN: ...Iniciando...")
				# Open and click on "Continuar" button
				if BotScraping.webdriver == None:
					Utils.printx ("+++ CODEBIN: Cargando nuevamente el webdriver...")
					BotScraping.startWebdriver ()
				self.webdriver = BotScraping.webdriver
		except Exception as ex:
			Utils.printException (ex)
			raise EcudocConnectionNotOpenException ()

	#-- Keep downloading same type documents
	def downloadingSameTypeDocs (self):
		if BotScraping.webdriver and BotScraping.DOC_FOUND \
		   and BotScraping.IS_OPEN and BotScraping.LAST_PAIS == pais:
			return True

		return False

	#-------------------------------------------------------------------
	# Return settings for acceding to CODEBIN documents
	#-------------------------------------------------------------------
	def getCodebinUrlSettingsForEmpresa (self):
		prefix = None
		if self.empresa == "BYZA":
			prefix = "byza"
		elif self.empresa == "NTA":
			prefix = "alcomexcargo"
		elif self.empresa == "LOGITRANS":
			prefix = "logitrans"
		else:
			raise Exception ("Empresa desconocida")
		

		settings = {}
		if self.docType == "CARTAPORTE":
			settings ["link"]    = f"https://{prefix}.corebd.net/1.cpi/nuevo.cpi.php?modo=3&idunico=%s"
			settings ["menu"]    = "Carta Porte I"
			settings ["submenu"] = "1.cpi/lista.cpi.php?todos=todos"
			settings ["prefix"]  = "CPI"

		elif self.docType == "MANIFIESTO":
			settings ["link"]    = f"https://{prefix}.corebd.net/2.mci/nuevo.mci.php?modo=3&idunico=%s"
			settings ["menu"]    = "Manifiesto de Carga"
			settings ["submenu"] = "2.mci/lista.mci.php?todos=todos"
			settings ["prefix"]  = "MCI"
		else:
			print ("Tipo de documento no soportado:", self.docType)
		return settings


	#-------------------------------------------------------------------
	# Get a list of cartaportes from range of ids
	#-------------------------------------------------------------------
	def getValuesFromRangeCodebinCartaportes (self, pais):
		self.docType = "CARTAPORTE"
		self.loginCodebin (pais)
		linkCartaporte = "https://byza.corebd.net/1.cpi/nuevo.cpi.php?modo=3&idunico=%s"

		for docId in range (121, 7075):
			docLink = linkCartaporte % docId
			self.webdriver.get (docLink)

			docForm = self.webdriver.find_element (By.TAG_NAME, "form")
			self.createParamsFileFromCodebinForm (docForm)

	#----------------------------------------------------
	# Create params file: 
	#   {paramsField: {ecudocField, codebinField, value}}
	#----------------------------------------------------
	def createParamsFileFromCodebinForm (self, docForm):
		#fields  = self.getParamFields () 
		fields = Utils.getParamFieldsForDocument (self.docType)
		for key in fields.keys():
			codebinField = fields [key]["codebinField"]
			try:
				elem = docForm.find_element (By.NAME, codebinField)
				fields [key]["value"] = elem.get_attribute ("value")
			except NoSuchElementException:
				#print (f"...Elemento '{codebinField}'  no existe")
				pass

		pais, codigo = "NONE", "NO" 
		textsWithCountry = [fields[x]["value"] for x in ["txt02"]]
		if any (["COLOMBIA" in x.upper() for x in textsWithCountry]):
			pais, codigo = "COLOMBIA", "CO"
		elif any (["ECUADOR" in x.upper() for x in textsWithCountry]):
			pais, codigo = "ECUADOR", "EC"
		elif any (["PERU" in x.upper() for x in textsWithCountry]):
			pais, codigo = "PERU", "PE"
			

		fields ["txt0a"]["value"] = pais

		docNumber = f"{codigo}{fields ['numero']['value']}"
		fields ["numero"]["value"] = docNumber
		fields ["txt00"]["value"]  = docNumber
		jsonFilename = f"CPI-{self.empresa}-{docNumber}-PARAMSFIELDS.json"
		json.dump (fields, open (jsonFilename, "w"), indent=4, default=str)


	#----------------------------------------------------------------
	#----------------------------------------------------------------
	def getEcudocCodebinFields (self):
		try:
			inputsParamsFile = Utils.getInputsParametersFile (self.docType)
			inputsParams     = ResourceLoader.loadJson ("docs", self.inputsParams)
			fields           = {}
			for key in inputsParams:
				ecudocsField = inputsParams [key]["ecudocsField"]
				codebinField = inputsParams [key]["codebinField"]
				if codebinField:
					fields [ecudocsField]  = {"codebinField":codebinField, "value":""}

			if self.docType == "CARTAPORTE":
				fields ["id"]             = {"codebinField":"idcpic", "value":""}
				fields ["fecha_creacion"] = {"codebinField":"cpicfechac", "value":""}
				fields ["referencia"]     = {"codebinField":"ref", "value":""}

			return fields
		except: 
			raise Exception ("Obteniendo campos de CODEBIN")

	#-------------------------------------------------------------------
	#-------------------------------------------------------------------
	def transmitFileToCodebin (self, codebinFieldsFile):
		docType = Utils.getDocumentTypeFromFilename (codebinFieldsFile)
		Utils.printx (f">> Transmitiendo '{docType}' a codebin")
		codebinFields = json.load (open (codebinFieldsFile))
		pais = codebinFields.pop ("pais")

		self.loginCodebin (pais)
		if docType == "CARTAPORTE":
			docFrame = self.getDocumentFrame ("frame", "Carta Porte", "1", "cpi", "nuevo")
		elif docType == "MANIFIESTO":
			docFrame = self.getDocumentFrame ("frame", "Manifiesto de Carga", "2", "mci", "nuevo")

		self.fillForm (docFrame, codebinFields)

	#-----------------------------------------------
	# Get links elements from document
	#-----------------------------------------------
	def printLinksFromDocument (self, docFrame):
		elements = docFrame.find_elements (By.XPATH, "//a")
		for elem in elements:
			print ("--", elem)
			print ("----", elem.get_attribute ("text"))

	#-------------------------------------------------------------------
	# Click "Cartaporte"|"Manifiesto" then "Nuevo" returning document frame
	#-------------------------------------------------------------------
	def getDocumentFrame (self, tagName, menuStr, optionNum, itemStr, functionStr):
		try:
			iniLink = self.webdriver.find_element (By.PARTIAL_LINK_TEXT, menuStr)
			iniLink.click()

			# Open frame
			#linkString = f"//a[contains(@href, '{optionNum}.{itemStr}/nuevo.{itemStr}.php?modo=1')]"
			#linkString = f"//a[contains(@href, '{optionNum}.{itemStr}/{functionStr}.{itemStr}.php?todos=todos')]"
			linkString = f"//a[contains(@href, '{optionNum}.{itemStr}/{functionStr}.{itemStr}.php?todos=todos')]"
			print ("-- linkString:", linkString)
			iniLink = self.webdriver.find_element (By.XPATH, linkString)
			iniLink.click()

			# Switch to the frame or window containing the <object> element
			object_frame = self.webdriver.find_element (By.TAG_NAME, "object")
			print ("-- object frame:", object_frame)
			wait = WebDriverWait (self.webdriver, 2)  # Adjust the timeout as needed
			wait.until (EC.frame_to_be_available_and_switch_to_it (object_frame))

			self.printLinksFromDocument (object_frame)
			print ("-- Waiting for form...")

			# Explicitly wait for the form to be located
			docForm = WebDriverWait(self.webdriver, 10).until(
				EC.presence_of_element_located((By.TAG_NAME, tagName))
			)

			return docForm
		except Exception as e:
			Utils.printx("No se pudo crear document nuevo en el CODEBIN")
			return None

	#-----------------------------------------------------------
	#-- Fill CODEBIN form fields with ECUDOC fields
	#-----------------------------------------------------------
	def fillForm (self, docForm, codebinFields):
		CARTAPORTE  = self.docType == "CARTAPORTE"
		MANIFIESTO  = self.docType == "MANIFIESTO"
		DECLARACION = self.docType == "DECLARACION"

		for field in codebinFields.keys():
			value = codebinFields [field]
			if not value:
				continue

			# Reception data copied to the others fields
			if CARTAPORTE and field in ["lugar2", "lugaremision"]:
				continue

			# Totals calculated automatically
			elif CARTAPORTE and field in ["totalmr", "monedat", "totalmd", "monedat2"]:
				continue

			# Radio button group
			elif MANIFIESTO and "radio" in field:
				elem = docForm.find_element (By.ID, field)
				self.wedriver.execute_script("arguments[0].click();", elem)

			# Tomados de la BD del vehículo y de la BD del conductor
			elif MANIFIESTO and field in ["a9", "a10", "a11", "a12"] and \
				field in ["a19", "a20", "a21", "a22"]:
				continue  

			# Tomados de la BD de la cartaporte
			elif MANIFIESTO and field in ["a29","a30","a31","a32a","a32b",
			                              "a33","a34a","a34b","a34c","a34d","a40"]:
				continue  

			else:
				elem = docForm.find_element (By.NAME, field)
				#elem.click ()
				elem.send_keys (value.replace ("\r\n", "\n"))

	#-----------------------------------------------------------
	#-- Get CODEBIN values from form with ECUDOC fields
	#-----------------------------------------------------------
	def getDataFromForm (self, docForm, codebinFields):
		CARTAPORTE  = self.docType == "CARTAPORTE"
		MANIFIESTO  = self.docType == "MANIFIESTO"
		DECLARACION = self.docType == "DECLARACION"

		for field in codebinFields.keys():
			value = codebinFields [field]
			if not value:
				continue

			# Reception data copied to the others fields
			if CARTAPORTE and field in ["lugar2", "lugaremision"]:
				continue

			# Totals calculated automatically
			elif CARTAPORTE and field in ["totalmr", "monedat", "totalmd", "monedat2"]:
				continue

			# Radio button group
			elif MANIFIESTO and "radio" in field:
				elem = docForm.find_element (By.ID, field)
				self.wedriver.execute_script("arguments[0].click();", elem)

			# Tomados de la BD del vehículo y de la BD del conductor
			elif MANIFIESTO and field in ["a9", "a10", "a11", "a12"] and \
				field in ["a19", "a20", "a21", "a22"]:
				continue  

			# Tomados de la BD de la cartaporte
			elif MANIFIESTO and field in ["a29","a30","a31","a32a","a32b",
			                              "a33","a34a","a34b","a34c","a34d","a40"]:
				continue  

			else:
				elem = docForm.find_element (By.NAME, field)
				#elem.click ()
				elem.send_keys (value.replace ("\r\n", "\n"))

	#-------------------------------------------------------------------
	# Close initial codebin windows
	#-------------------------------------------------------------------
	def closeInitialCodebinWindow (self):
		print ("-- Cerrando ventana inicial de CODEBIN")
		# Store the handle of the original window
		original_window = self.webdriver.current_window_handle	

		for handle in self.webdriver.window_handles:
			self.webdriver.switch_to.window (handle)
			current_title = self.webdriver.title

			if "GRUPO BYZA SAS" in current_title or \
			"NUEVO TRANSPORTE DE AMERICA CIA LTDA" in current_title:
				self.webdriver.close()  # Close the window with the matching title
				break  # Exit the loop once the target window is closed		

		self.webdriver.switch_to.window (original_window)

#	#-------------------------------------------------------------------
#	# Get the number (ej. CO00902, EC03455) from the filename
#	#-------------------------------------------------------------------
#	def getDocumentNumberFromFilename (self, filename):
#		numbers = re.findall (r"\w+\d+", filename)
#		docNumber = numbers [-1]
#
#		docNumber = docNumber.replace ("COCO", "CO")
#		docNumber = docNumber.replace ("ECEC", "EC")
#		docNumber = docNumber.replace ("PEPE", "PE")
#
#		return docNumber
#
#	#----------------------------------------------------------------
#	#-- Create CODEBIN fields from document fields using input parameters
#	#-- Add three new fields: idcpic, cpicfechac, ref
#	#----------------------------------------------------------------
#	def getParamFields (self):
#		try:
#			inputsParamsFile = Utils.getInputsParametersFile (self.docType)
#			inputsParams     = ResourceLoader.loadJson ("docs", inputsParamsFile)
#			fields           = {}
#			for key in inputsParams:
#				ecudocsField  = inputsParams [key]["ecudocsField"]
#				codebinField = inputsParams [key]["codebinField"]
#				fields [key] = {"ecudocsField":ecudocsField, "codebinField":codebinField, "value":""}
#
#			if self.docType == "CARTAPORTE":
#				fields ["id"]             = {"ecudocsField":"id", "codebinField":"idcpic", "value":""}
#				fields ["numero"]         = {"ecudocsField":"numero", "codebinField":"nocpic", "value":""}
#				fields ["fecha_creacion"] = {"ecudocsField":"fecha_creacion", "codebinField":"cpicfechac", "value":""}
#				fields ["referencia"]     = {"ecudocsField": "referencia", "codebinField":"ref", "value":""}
#
#			return fields
#
#		except: 
#			raise Exception ("Obteniendo campos de CODEBIN")
#



#----------------------------------------------------------
# Remove invalid CODEBIN JSON files for cartaportes 
#----------------------------------------------------------
def cleanCodebinCartaportesFiles (inDir):
	files       = os.listdir (inDir)
	invalidDir  = f"{inDir}/invalid"
	os.system (f"mkdir {invalidDir}")
	pathFiles   = [f"{inDir}/{x}" for x in files if "invalid" not in x]
	for path in pathFiles:

		print ("-- path:", path)
		data = json.load (open (path))
		subjectFields = ["txt02", "txt03", "txt04", "txt05", "txt06", "txt07", "txt08", "txt19"]
		if any ([data [x]["value"].strip()=="" for x in subjectFields]):
			os.system (f"mv {path} {invalidDir}")

#----------------------------------------------------------------
# Needs to update parameters
# startCodebinBot
#----------------------------------------------------------------
def startCodebinBot (docType, codebinFieldsFile):
	botCodebin = BotScraping (docType, codebinFieldsFile)
	botCodebin.transmitFileToCodebin (codebinFieldsFile)

#-----------------------------------------------------------
# Call to main
#-----------------------------------------------------------
if __name__ == "__main__":
	main()
