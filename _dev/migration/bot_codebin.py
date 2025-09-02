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

#----------------------------------------------------------
# Main
#----------------------------------------------------------
def main ():
	args = sys.argv
	option = args [1]
	print ("--option:", option)

	if "--getEcudocsValues" in option:
		print (">> Running getEcudocsValues...")
		pdfFilepath = args [2]
		codebinBot = CodebinBot ("BYZA")
		codebinBot.getEcudocsValuesFromCodebinWeb (pdfFilepath)
		
	elif "--getcodebinvalues" in option:
		#---- Extract data from CODEBIN --------------------------------- 
		botCodebin = CodebinBot ()
		botCodebin.getValuesFromRangeCodebinCartaportes ("colombia")

	elif "--cleancodebincartaportes" in option:
		#---- Remove invalid records (e.g. no remitente)
		inDir = args [2]
		cleanCodebinCartaportesFiles (inDir)

#----------------------------------------------------------------
# Bot for filling CODEBIN forms from ECUDOCS fields info
#----------------------------------------------------------------
class CodebinBot:
	def __init__ (self, pdfFilepath, settings, webdriver):
		self.settings = settings
		self.empresa  = settings ["empresa"]
		self.url      = settings ["urlCodebin"]
		#self.user     = settings ["userColombia"]
		#self.password = settings ["passwordColombia"]

		# Init bot settings
		self.docNumber             = self.getDocumentNumberFromFilename (pdfFilepath) # Special for NTA
		self.docType               = Utils.getDocumentTypeFromFilename (pdfFilepath)
		self.pais, self.codigoPais = Utils.getPaisCodigoFromDocNumber (self.docNumber)
		self.user, self.password   = self.getUserPasswordForPais (self.pais)

		self.webdriver             = CodebinBot.webdriver

	#------------------------------------------------------
	# Used 
	#------------------------------------------------------
	@staticmethod
	def getWaitWebdriver (DEBUG=False):
		Utils.printx ("Getting webdriver...")
		if DEBUG:
			CodebinBot.webdriver = None


		while not hasattr (CodebinBot, "webdriver"):
			Utils.printx ("...Loading webdriver...")
			options = Options()
			options.add_argument("--headless")
			CodebinBot.IS_OPEN = False
			CodebinBot.LAST_PAIS = ""
			CodebinBot.DOC_FOUND = False
			CodebinBot.webdriver = webdriver.Firefox (options=options)
			#CodebinBot.webdriver = webdriver.Firefox ()
			Utils.printx ("...Webdriver Loaded")
		return CodebinBot.webdriver

	#------------------------------------------------------
	# Public method called from EcuDoc
	# Return doc file with doc fields (old azr fields)
	#------------------------------------------------------
	def getDocumentFile (self):
		try:
			# Call to bot to get values from CODEBIN web
			codebinValues = None
			codebinValues = self.getValuesFromCodebinWeb (self.docNumber, self.pais, self.codigoPais)

			# Format to Azure values
			azureValues = Utils.getAzureValuesFromCodebinValues (self.docType, codebinValues, self.docNumber)
			# Save data
			outCbinFilename = f"{self.docType}-{self.empresa}-{self.docNumber}-CBINFIELDS.json"
			outDocFilename  = f"{self.docType}-{self.empresa}-{self.docNumber}-DOCFIELDS.json"
			json.dump (codebinValues, open (outCbinFilename, "w"), indent=4)
			json.dump (azureValues, open (outDocFilename, "w"), indent=4, sort_keys=True)

			CodebinBot.DOC_FOUND = True
			CodebinBot.LAST_PAIS = self.pais
			CodebinBot.IS_OPEN   = True
			return outDocFilename
		except EcudocDocumentNotFoundException:
			CodebinBot.DOC_FOUND = False
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
	#------------------------------------------------------
	def getUserPasswordForPais (self, pais):
		user, password = None, None
		if pais.upper() == "COLOMBIA":
			user      = self.settings ["userColombia"]
			password  = self.settings ["passwordColombia"]
		elif pais.upper() == "ECUADOR":
			user      = self.settings ["userEcuador"]
			password  = self.settings ["passwordEcuador"]
		elif pais.upper() == "PERU":
			user      = self.settings ["userPeru"]
			password  = self.settings ["passwordPeru"]
		else:
			raise Exception (Utils.printx (f"No se asigno user/password. Pais no existente:", pais))

		return user, password

	#-------------------------------------------------------------------
	# Get the number (ej. CO00902, EC03455) from the filename
	#-------------------------------------------------------------------
	def getDocumentNumberFromFilename (self, filename):
		numbers = re.findall (r"\w+\d+", filename)
		docNumber = numbers [-1]

		docNumber = docNumber.replace ("COCO", "CO")
		docNumber = docNumber.replace ("ECEC", "EC")
		docNumber = docNumber.replace ("PEPE", "PE")

		return docNumber

	#-------------------------------------------------------------------
	#-- Get the CODEBIN id from document number
	#-- List documents, search the number, and get the id of selected
	#-------------------------------------------------------------------
	def getValuesFromCodebinWeb (self, docNumber, pais, codigoPais):
		self.openCodebin (pais)

		urlSettings  = self.getCodebinUrlSettingsForEmpresa ()
		textMainmenu = urlSettings ["menu"]
		textSubmenu  = urlSettings ["submenu"]
		documentUrl  = urlSettings ["link"]

		searchField, docsTable = self.getCodebinSearchElements (textMainmenu, textSubmenu) 
		searchField.send_keys (docNumber)

		# Get table, get row, and extract id
		docId = self.getCodebinDocumentId (docsTable, docNumber)

		# Get CODEBIN link for document with docId
		self.webdriver.get (documentUrl % docId)

		# Get Codebin values from document form
		docForm       = self.webdriver.find_element (By.TAG_NAME, "form")
		codebinValues = self.getCodebinValuesFromCodebinForm (docForm, codigoPais, docNumber)

		self.closeInitialCodebinWindow ()
		return codebinValues

	#-------------------------------------------------------------------
	#-------------------------------------------------------------------
	def getCodebinDocumentId (self, docsTable, docNumber):
		docId   = None
		message = f"Documento '{docNumber}' no encontrado"
		try:
			#table   = container.find_element (By.TAG_NAME, "table")
			docLink    = docsTable.find_element (By.PARTIAL_LINK_TEXT, docNumber)
			idText     = docLink.get_attribute ("onclick")
			textLink   = docLink.text
			docId      = re.findall (r"\d+", idText)[-1]

			Utils.printx (f"+++ CODEBIN: ...Documento buscado: '{docNumber}' : Documento encontrado: '{textLink}'")
			if docNumber != textLink.strip():
				raise EcudocDocumentNotFoundException (message)
		except NoSuchElementException:
			raise EcudocDocumentNotFoundException (message)
		except:
			raise
		return docId

	#-------------------------------------------------------------------
	#-------------------------------------------------------------------
	def quitCodebin (self):
		#-- Webdriver is killed by the main function as it is an independent thread
		if CodebinBot.webdriver:
			print ("+++ CODEBIN: ...Quitando driver")
			CodebinBot.webdriver.quit ()

		Utils.printx ("+++ CODEBIN: ...Reiniciando variables")
		CodebinBot.IS_OPEN   = False
		CodebinBot.LAST_PAIS = ""
		CodebinBot.DOC_FOUND = False
		CodebinBot.webdriver = None
		self.webdriver       = None

	#-------------------------------------------------------------------
	#-------------------------------------------------------------------
	def getCodebinSearchElements (self, textMainmenu, textSubmenu):
		wait = WebDriverWait (self.webdriver, 5)
		# Select menu Carta Porte I
		cpi = wait.until (EC.presence_of_element_located ((By.PARTIAL_LINK_TEXT, textMainmenu)))
		cpi.click ()

		# Select submenu 'Lista'
		cpi_lista = wait.until (EC.presence_of_element_located ((By.XPATH, f"//a[contains(@href, '{textSubmenu}')]")))
		cpi_lista.click ()

		# Get and swithc to frame 'Lista'
		cpi_lista_object = wait.until (EC.presence_of_element_located ((By.TAG_NAME, "object")))

		wait.until (EC.frame_to_be_available_and_switch_to_it (cpi_lista_object))
		time.sleep (1)

		# get and set number into input 'Buscar'
		cpi_lista_container = self.webdriver.find_elements (By.CLASS_NAME, "container")
		container           = cpi_lista_container [0]

		# get the input search field
		searchField    = wait.until (EC.presence_of_element_located ((By.TAG_NAME, "input")))
		searchTable    = wait.until (EC.presence_of_element_located ((By.TAG_NAME, "table")))

		return searchField, searchTable 

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

	#-------------------------------------------------------------------
	# Initial browser opening
	# Open codebin session for new docs or go back to begina a new search
	#-------------------------------------------------------------------
	def openCodebin (self, pais):
		try:
			print ("+++ CODEBIN: ...Obteniendo valores ")
			cb = CodebinBot
			print (f"  ...IS_OPEN: {cb.IS_OPEN}. LAST_PAIS: {cb.LAST_PAIS}, DOC_FOUND: {cb.DOC_FOUND}")
			print (f"  ...WEBDRIVER: {CodebinBot.webdriver}")
			print (f"  ...webdriver: {self.webdriver}")

			if CodebinBot.webdriver and CodebinBot.DOC_FOUND \
			   and CodebinBot.IS_OPEN and CodebinBot.LAST_PAIS == pais:
				print ("+++ CODEBIN: ...Regresando...")
				self.webdriver.back ()    # Search results
			else:
				print ("+++ CODEBIN: ...Iniciando...")
				# Open and click on "Continuar" button
				if CodebinBot.webdriver == None:
					Utils.printx ("+++ CODEBIN: ...AutenticAndose nuevamente...")
					options = Options()
					options.add_argument("--headless")
					CodebinBot.webdriver = webdriver.Firefox (options=options)
					print (f"+++ CODEBIN:  ...Nuevo webdriver: {CodebinBot.webdriver}")
					self.webdriver = CodebinBot.webdriver

				self.enterCodebin ()
				self.loginCodebin (pais)
				CodebinBot.IS_OPEN = True
				CodebinBot.LAST_PAIS = pais
				CodebinBot.DOC_FOUND = False
		except Exception as ex:
			Utils.printException (ex)
			raise EcudocConnectionNotOpenException ()

	#-------------------------------------------------------------------
	# Codebin enter session: open URL and click into "Continuar" button
	#-------------------------------------------------------------------
	def enterCodebin (self):
		print ("+++ CODEBIN: ...Ingresando URL ...")
		#self.webdriver.get ("https://www.google.com/")
		self.webdriver.get (self.url)
		#self.webdriver.get ("https://byza.corebd.net")
		submit_button = self.webdriver.find_element(By.XPATH, "//input[@type='submit']")
		submit_button.click()

		# Open new window with login form, then switch to it
		time.sleep (2)
		winMenu = self.webdriver.window_handles [-1]
		self.webdriver.switch_to.window (winMenu)

	#-------------------------------------------------------------------
	# Returns the web driver after login into CODEBIN
	#-------------------------------------------------------------------
	def loginCodebin (self, pais):
		print (f"+++ CODEBIN: ...AutenticAndose con paIs : '{pais}'")
		# Login Form : fill user / password
		loginForm = self.webdriver.find_element (By.TAG_NAME, "form")
		userInput = loginForm.find_element (By.NAME, "user")
		#userInput.send_keys ("GRUPO BYZA")
		userInput.send_keys (self.user)
		pswdInput = loginForm.find_element (By.NAME, "pass")
		#pswdInput.send_keys ("GrupoByza2020*")
		pswdInput.send_keys (self.password)

		# Login Form:  Select pais (Importación or Exportación : Colombia or Ecuador)
		docSelectElement = self.webdriver.find_element (By.XPATH, "//select[@id='tipodoc']")
		docSelect = Select (docSelectElement)
		docSelect.select_by_value (pais)
		submit_button = loginForm.find_element (By.XPATH, "//input[@type='submit']")
		submit_button.click()

		return self.webdriver

	#----------------------------------------------------
	# Get codebin fields : {codebinField:value}
	#----------------------------------------------------
	def getCodebinValuesFromCodebinForm (self, docForm, codigoPais, docNumber):
		fields  = self.getParamFields () 
		codebinValues = {}
		for key in fields.keys():
			codebinField = fields [key]["codebinField"]
			try:
				elem = docForm.find_element (By.NAME, codebinField)
				value = elem.get_attribute ("value")
				codebinValues [codebinField] = value
			except NoSuchElementException:
				print (f"...Elemento '{codebinField}'  no existe")
				pass

		# For MANIFIESTO: Get selected radio button 
		if self.docType == "CARTAPORTE":
			codebinValues ["nocpic"] = docNumber
		elif self.docType == "MANIFIESTO":
			codebinValues ["no"] = docNumber

			radio_group = docForm.find_elements (By.NAME, "r25")  # Assuming radio buttons have name="size"
			for radio_button in radio_group:
				codebinField = radio_button.get_attribute('id')
				if radio_button.is_selected():
					codebinValues [codebinField] = "X"
				else:
					codebinValues [codebinField] = ""

		return codebinValues

	#-------------------------------------------------------------------
	# Return settings for acceding to CODEBIN documents
	#-------------------------------------------------------------------
	def getCodebinUrlSettingsForEmpresa (self):
		prefix = None
		if self.empresa == "BYZA":
			prefix = "byza"
		elif self.empresa == "NTA":
			prefix = "nta"
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
		fields  = self.getParamFields () 
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
	#-- Create CODEBIN fields from document fields using input parameters
	#-- Add three new fields: idcpic, cpicfechac, ref
	#----------------------------------------------------------------
	def getParamFields (self):
		try:
			inputsParamsFile = self.getInputParametersFile ()
			inputsParams     = ResourceLoader.loadJson ("docs", inputsParamsFile)
			fields           = {}
			for key in inputsParams:
				ecudocsField  = inputsParams [key]["ecudocsField"]
				codebinField = inputsParams [key]["codebinField"]
				fields [key] = {"ecudocsField":ecudocsField, "codebinField":codebinField, "value":""}

			if self.docType == "CARTAPORTE":
				fields ["id"]             = {"ecudocsField":"id", "codebinField":"idcpic", "value":""}
				fields ["numero"]         = {"ecudocsField":"numero", "codebinField":"nocpic", "value":""}
				fields ["fecha_creacion"] = {"ecudocsField":"fecha_creacion", "codebinField":"cpicfechac", "value":""}
				fields ["referencia"]     = {"ecudocsField": "referencia", "codebinField":"ref", "value":""}

			return fields
		except: 
			raise Exception ("Obteniendo campos de CODEBIN")

	#----------------------------------------------------------------
	#----------------------------------------------------------------
	def getEcudocCodebinFields (self):
		try:
			inputsParamsFile = self.getInputParametersFile ()
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

	#-------------------------------------------------------
	#-- Return input parameters file
	#-------------------------------------------------------
	def getInputParametersFile (self):
		if self.docType == "CARTAPORTE":
			self.inputsParams = "cartaporte_input_parameters.json"
		elif self.docType == "MANIFIESTO":
			self.inputsParams = "manifiesto_input_parameters.json"
		elif self.docType == "DECLARACION":
			self.inputsParams = "declaracion_input_parameters.json"
		else:
			message= f"ERROR: Tipo de documento desconocido:", docType
			raise Exception (message)
		return self.inputsParams
	
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
	botCodebin = CodebinBot (docType, codebinFieldsFile)
	botCodebin.transmitFileToCodebin (codebinFieldsFile)

#-----------------------------------------------------------
# Call to main
#-----------------------------------------------------------
if __name__ == "__main__":
	main()
