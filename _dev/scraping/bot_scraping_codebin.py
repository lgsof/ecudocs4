#!/usr/bin/env python3
import os, sys, re, time

from ecuapassdocs.info.ecuapass_utils import Utils
from ecuapass_exceptions import EcudocDocumentNotFoundException, EcudocConnectionNotOpenException

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


from bot_scraping import BotScraping
from ecuapass_settings import EcuSettings

#----------------------------------------------------------
# Main
#----------------------------------------------------------
def main ():
	args = sys.argv
	option = args [1]
	print ("--option:", option)

	# Load "empresa": reads and checks if "settings.txt" file exists')
	runningDir     = os.getcwd ()
	ecuSettings    = EcuSettings (runningDir)
	credentials    = ecuSettings.readBinSettings ()
	empresa        = credentials ["empresa"]

	if "--download" in option:
		print (">> Running getEcudocsValues...")
		pdfFilepath       = args [2]
		webdriver         = BotScrapingCodebin.loadWebdriver ()
		botCodebin        = BotScrapingCodebin (pdfFilepath, credentials, webdriver)
		docFieldsFilename = botCodebin.downloadDocument ()
		
	elif "--getcodebinvalues" in option:
		#---- Extract data from CODEBIN --------------------------------- 
		botCodebin = BotScrapping ()
		botCodebin.getValuesFromRangeCodebinCartaportes ("colombia")

	elif "--cleancodebincartaportes" in option:
		#---- Remove invalid records (e.g. no remitente)
		inDir = args [2]
		cleanCodebinCartaportesFiles (inDir)

#----------------------------------------------------------
# Bot for web scraping of Codebin documents
#----------------------------------------------------------
class BotScrapingCodebin (BotScraping):
	def __init__ (self, pdfFilepath, credentials, webdriver):
		super().__init__ (pdfFilepath, credentials, webdriver)

	#----------------------------------------------------
	# Get codebin fields : {codebinField:value}
	#----------------------------------------------------
	def getVauesFromForm (self, docForm, codigoPais, docNumber):
		#fields  = self.getParamFields () 
		fields = Utils.getParamFieldsForDocument (self.docType)
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
	# Navigate to document search table from Codebin menu and submenu
	#-------------------------------------------------------------------
	def locateSearchSite (self, urlSettings):
		textMainmenu = urlSettings ["menu"]
		textSubmenu  = urlSettings ["submenu"]

		wait = WebDriverWait (self.webdriver, 5)
		# Select menu Carta Porte I
		cpi = wait.until (EC.presence_of_element_located ((By.PARTIAL_LINK_TEXT, textMainmenu)))
		cpi.click ()

		# Select submenu 'Lista'
		cpi_lista = wait.until (EC.presence_of_element_located ((By.XPATH, f"//a[contains(@href, '{textSubmenu}')]")))
		cpi_lista.click ()

		# Get and switch to frame 'Lista'
		cpi_lista_object = wait.until (EC.presence_of_element_located ((By.TAG_NAME, "object")))

		wait.until (EC.frame_to_be_available_and_switch_to_it (cpi_lista_object))
		time.sleep (1)

	#-------------------------------------------------------------------
	# Return document form with their values
	#-------------------------------------------------------------------
	def searchDocumentInSite (self, urlSettings, docNumber):
		# get the input search field
		wait         = WebDriverWait (self.webdriver, 5)
		searchField  = wait.until (EC.presence_of_element_located ((By.TAG_NAME, "input")))
		docsTable    = wait.until (EC.presence_of_element_located ((By.TAG_NAME, "table")))

		searchField.send_keys (docNumber)

		# Get table, get row, and extract id
		docId = self.getCodebinDocumentId (docsTable, docNumber)

		# Get CODEBIN link for document with docId
		documentUrl  = urlSettings ["link"]
		self.webdriver.get (documentUrl % docId)

		# Get Codebin values from document form
		docForm       = self.webdriver.find_element (By.TAG_NAME, "form")
		return docForm

	#-------------------------------------------------------------------
	# Codebin enter session: open URL and click into "Continuar" button
	#-------------------------------------------------------------------
	def openCodebin (self):
		try:
			Utils.printx ("+++ CODEBIN: ...Autenticándose nuevamente...")
			#self.openCodebin ()
			print ("+++ CODEBIN: ...Ingresando URL ...")
			self.webdriver.get (self.url)
			submit_button = self.webdriver.find_element(By.XPATH, "//input[@type='submit']")
			submit_button.click()

			# Open new window with login form, then switch to it
			time.sleep (2)
			winMenu = self.webdriver.window_handles [-1]
			self.webdriver.switch_to.window (winMenu)

		except Exception as ex:
			Utils.printException (ex)
			raise EcudocConnectionNotOpenException ()

	#-------------------------------------------------------------------
	# Returns the web driver after login into CODEBIN
	#-------------------------------------------------------------------
	def loginCodebin (self, pais):
		print (f"+++ CODEBIN: ...AutenticAndose con paIs : '{pais}'")
		# Login Form : fill user / password
		loginForm = self.webdriver.find_element (By.TAG_NAME, "form")
		userInput = loginForm.find_element (By.NAME, "user")
		userInput.send_keys (self.user)
		pswdInput = loginForm.find_element (By.NAME, "pass")
		pswdInput.send_keys (self.password)

		# Login Form:  Select pais (Importación or Exportación : Colombia or Ecuador)
		docSelectElement = self.webdriver.find_element (By.XPATH, "//select[@id='tipodoc']")
		docSelect = Select (docSelectElement)
		docSelect.select_by_value (pais)
		submit_button = loginForm.find_element (By.XPATH, "//input[@type='submit']")
		submit_button.click()


		# Set flags
		BotScraping.IS_OPEN = True
		BotScraping.LAST_PAIS = pais
		BotScraping.DOC_FOUND = False
		return self.webdriver

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


#-----------------------------------------------------------
# Call to main
#-----------------------------------------------------------
if __name__ == "__main__":
	main()
