#!/usr/bin/env python3
"""
Bot for migration of CODEBIN documents in the contex of the EcuapassDocs Web App
Downloads docs from Codebin, Save Codebin docs to DB, Update existe DB relations
"""

import json, time, sys, os, random

#----------------------------------------------------------
from app_cartaporte.models_cpi import Cartaporte, CartaporteForm
from app_manifiesto.models_mci import Manifiesto, ManifiestoForm
from app_declaracion.models_dti import Declaracion, DeclaracionForm
from app_usuarios.models import Usuario
from app_docs.models_Scripts import Scripts    # saveNewDocToDB

from ecuapassdocs.info.ecuapass_utils import Utils
from ecuapassdocs.info.ecuapass_extractor import Extractor
from ecuapassdocs.info.ecuapass_data import EcuData
from ecuapassdocs.info.resourceloader import ResourceLoader
#----------------------------------------------------------
from bot_migration_docs import docs
#----------------------------------------------------------
import django
os.environ.setdefault ("DJANGO_SETTINGS_MODULE", "app_main.settings") #appdocs_main") #/settings")
APPDOCS_PATH = "/ecuapp/ecuapassdocs3/app/"
sys.path.append (f"{APPDOCS_PATH}")
django.setup ()
#----------------------------------------------------------

USAGE="""\n
bot_migration.py --[save|download|update] <InputDir> [pattern]
\n"""

#----------------------------------------------------------
# main
#----------------------------------------------------------
def main ():
	args   = sys.argv
	if len (args) == 1:
		print (USAGE)
		sys.exit (0)

	option = args [1]
	if option == "--save":
		inputDir = args [2]
		pattern  = args [3]
		saveDocs (inputDir, pattern)
	elif option == "--download":
		inputDir = args [2]
		downloadDocs (inputDir)
	elif option == "--update":
		updateDocs ()
	else:
		print ("Opción desconocida")

def updateDocs ():
	bot = BotMigration ("BYZA", "COLOMBIA", "MANIFIESTO", 0, 0, webdriver)
	bot.updateCurrentDBAssociations ()

#--------------------------------------------------------------------
# Save docs in JSON files to DB for empresa, pais, docType
# Save docs files (JSON) in input dir to DB
#--------------------------------------------------------------------
def saveDocs (inputDir, pattern=""):
	#webdriver = BotMigration.getWaitWebdriver (DEBUG=True)
	#bot = BotMigration ("LOGITRANS", "COLOMBIA", "DECLARACION", 0, 0, webdriver)
	#bot = BotMigration ("BYZA", "COLOMBIA", "MANIFIESTO", 0, 0, webdriver)
	#bot.saveDocFilesToDB ("BYZA", inputDir, pattern)

	empresa, pais, docType = getEmpresaPaisDocTypeFromName (inputDir)
	bot                    = BotMigration (empresa, pais, docType)
	migrationFilesList     = [f"{inputDir}/{x}" for x in Utils.getSortedFilesFromDir (inputDir)]
	migrationFilesList     = [x for x in migrationFilesList if pattern in x]

	for migrationFilename in migrationFilesList:
		formFields = Utils.getFormFieldsFromMigrationFieldsFile (migrationFilename)
		formFields = bot.addInfoEmpresa (empresa, formFields)
		usuario    = Usuario.objects.get (username=bot.usuario)
		bot.saveNewDocToDB (formFields, docType, pais, usuario)

#--------------------------------------------------------------------
# Get pais, empresa, pais from inputDir name (e.g. byza-2024-MCI-CO
#--------------------------------------------------------------------
def getEmpresaPaisDocTypeFromName (inputDir):
	parts     = os.path.basename (inputDir).split ("-")
	empresa   = parts [0].upper ()
	docType   = Utils.getDocumentTypeFromFilename (parts [2])
	paisCode  = parts [3]
	pais      = Utils.getPaisFromCodigoPais (paisCode)

	print (f"+++ empresa '{empresa}'")
	print (f"+++ pais '{pais}'")
	print (f"+++ docType '{docType}'")
	return empresa, pais, docType

#--------------------------------------------------------------------
#--------------------------------------------------------------------
def downloadDocs (inputDir):
	from selenium import webdriver
	from selenium.webdriver.firefox.service import Service
	from selenium.common.exceptions import NoSuchElementException
	from selenium.webdriver.firefox.options import Options
	from selenium.webdriver.common.by import By
	from selenium.webdriver.support.ui import Select

	from webdriver_manager.firefox import GeckoDriverManager
	from webdriver_manager.chrome import ChromeDriverManager

	webdriver = BotMigration.getWaitWebdriver (DEBUG=False)
	#------------------------ SETTINGS --------------------#
	#empresa, doctype, prefix, year, pais, code = "LOGITRANS", "CARTAPORTE", "CPI", "2024", "COLOMBIA", "CO"
	#empresa, doctype, prefix, year, pais, code = "BYZA", "CARTAPORTE", "CPI", "2024", "COLOMBIA", "CO"
	empresa, doctype, prefix, year, pais, code = "BYZA", "MANIFIESTO", "MCI", "2024", "COLOMBIA", "CO"
	#empresa, doctype, prefix, year, pais, code = "BYZA", "MANIFIESTO", "MCI", "2019", "COLOMBIA", "CO"
	INI = docs [f"{empresa}"][f"{year}-{code}-{prefix}"]["ini"]["id"]
	END = docs [f"{empresa}"][f"{year}-{code}-{prefix}"]["end"]["id"]
	bot = BotMigration (f"{empresa}", f"{pais}", f"{doctype}", INI, END, webdriver)
	#------------------------------------------------------#
	bot.enterCodebin ()
	bot.loginCodebin (bot.pais)
	bot.downloadDocuments (inputDir)
	webdriver.close()  # Close the window with the matching title

#--------------------------------------------------------------------
# Class with properties and functios for migration: dowload/save docs
#--------------------------------------------------------------------
class BotMigration:
	def __init__ (self, empresa, pais, docType, initialId=0, finalId=0, webdriver=None):
			self.empresa	= empresa
			self.pais	    = pais
			self.docType	= docType

			self.codigoPais = Utils.getCodigoPaisFromPais (pais)
			self.initialId	= initialId
			self.finalId	= finalId
			self.webdriver	= webdriver
			self.settings	= self.getCodebinSettingsForEmpresa ()
			self.usuario	= self.settings [pais]["user"]
			print (f"+++ usuario '{self.usuario}'")
			self.password	= self.settings [pais]["password"]
			self.docPrefix	= self.settings ["docPrefix"]
			
#			types = {
#				"CARTAPORTE" :{"doc":Cartaporte, "form":CartaporteForm},
#				"MANIFIESTO" :{"doc":Manifiesto, "form":ManifiestoForm},
#				"DECLARACION":{"doc":Declaracion, "form":DeclaracionForm}
#			}
#			self.DOCMODEL  = types[docType] ["doc"]
#			self.FORMMODEL = types[docType] ["form"]

	#-------------------------------------------------------------------
	# Get a list of cartaportes from range of ids
	#-------------------------------------------------------------------
	def downloadDocuments (self, outDir):
		try:
			os.system (f"mkdir {outDir}")
			urlLink = self.settings ["link"]

			failingDocs, successDocs, blankDocs  = [], [], []
			# Download from latest id to old id (reverse order)
			for docId in range (self.initialId, self.finalId - 1,  -1):
				try:
					docLink = urlLink % docId
					print (f"+++ docId: '{docId}'. docLink: '{docLink}'")
					self.webdriver.get (docLink)
					docForm = self.webdriver.find_element (By.TAG_NAME, "form")
					params, docNumber = self.extractMigrationFieldsFromCodebinForm (docForm)

					migrationFilename = f"{outDir}/{self.docPrefix}-{self.empresa}-{docNumber}-MIGRATIONFIELDS.json"
					print (f"+++ migrationFilename:  '{migrationFilename}'")
					json.dump (params, open (migrationFilename, "w"), indent=4, default=str)
					successDocs.append (f"{docId}\t{docNumber}")

					# Check blank docs
					print (f"+++ docNumber:  '{docNumber}'")
					if docNumber == None or docNumber == "":
						print (f"+++ BLANK ({len(blankDocs)}) : {docId}")
						blankDocs.append (docId)
						if len (blankDocs) > 5:
							break

					# Wait for the download to complete
					time.sleep (random.uniform(2, 4))  # Random delay to simulate human behavior
				except:
					Utils.printException ()
					failingDocs.append (str(docId))
				# Introduce random delay between requests
				#time.sleep (random.uniform(2, 5))

			failingDocsFilename = f"{outDir}/{self.docType}-FAILINGDOCS-{self.initialId}-{self.finalId}.txt"
			with open (failingDocsFilename, "w") as fp:
				for string in failingDocs:
					fp.write (string + "\n")

			successDocsFilename = f"{outDir}/{self.docType}-SUCCESSDOCS-{self.initialId}-{self.finalId}.txt"
			with open (successDocsFilename, "w") as fp:
				for string in successDocs:
					fp.write (string + "\n")
		except:
			Utils.printException ()

	#-------------------------------------------------------------------
	# Codebin enter session: open URL and click into "Continuar" button
	#-------------------------------------------------------------------
	def enterCodebin (self):
		print ("+++ CODEBIN: ...Ingresando URL ...")
		#self.webdriver.get ("https://www.google.com/")
		self.webdriver.get (self.settings ["urlCodebin"])
		#self.webdriver.get ("https://byza.corebd.net")
		submit_button = self.webdriver.find_element(By.XPATH, "//input[@type='submit']")
		submit_button.click()

		# Open new window with login form, then switch to it
		time.sleep (2)
		winMenu = self.webdriver.window_handles [-1]
		self.webdriver.switch_to.window (winMenu)

	#----------------------------------------------------
	# Create params file: 
	#	{paramsField: {ecudocField, codebinField, value}}
	#   Only works for Cartaporte
	#----------------------------------------------------
	def extractMigrationFieldsFromCodebinForm (self, docForm):
		params	= self.getParamsMigrationFields () 
		for key in params.keys():
			codebinField = params [key]["codebinField"]
			try:
				elem = docForm.find_element (By.NAME, codebinField)
				params [key]["value"] = elem.get_attribute ("value")
			except NoSuchElementException:
				#print (f"...Elemento '{codebinField}'	no existe")
				pass

		codigo = self.codigoPais
		params ["txt0a"]["value"] = codigo     # e.g. CO, EC, PE

		codebinNumber = params ['numero']['value']
		if codebinNumber == "" or codebinNumber is None:
			docNumber = ""
		else:
			docNumber = f"{codigo}{codebinNumber}"

		params ["numero"]["value"] = docNumber
		params ["txt00"]["value"]  = docNumber

		return params, docNumber

	#----------------------------------------------------------------
	#-- Create CODEBIN fields from document fields using input parameters
	#-- Add three new fields: idcpic, cpicfechac, ref
	#----------------------------------------------------------------
	def getParamsMigrationFields (self):
		try:
			inputsParamsFile = Utils.getInputsParametersFile (self.docType)
			inputsParams	 = ResourceLoader.loadJson ("docs", inputsParamsFile)
			fields			 = {}
			for key in inputsParams:
				ecudocsField  = inputsParams [key]["ecudocsField"]
				codebinField = inputsParams [key]["codebinField"]
				fields [key] = {"ecudocsField":ecudocsField, "codebinField":codebinField, "value":""}

			if self.docType == "CARTAPORTE":
				fields ["id"]			  = {"ecudocsField":"id", "codebinField":"idcpic", "value":""}
				fields ["numero"]		  = {"ecudocsField":"numero", "codebinField":"nocpic", "value":""}
				fields ["fecha_creacion"] = {"ecudocsField":"fecha_creacion", "codebinField":"cpicfechac", "value":""}
				fields ["referencia"]	  = {"ecudocsField": "referencia", "codebinField":"ref", "value":""}
			elif self.docType == "MANIFIESTO":
				fields ["id"]			  = {"ecudocsField":"id", "codebinField":"idmci", "value":""}
				fields ["numero"]		  = {"ecudocsField":"numero", "codebinField":"no", "value":""}
				fields ["fecha_creacion"] = {"ecudocsField":"fecha_creacion", "codebinField":"mcifechac", "value":""}
				fields ["referencia"]	  = {"ecudocsField": "referencia", "codebinField":"ref", "value":""}
			elif self.docType == "DECLARACION":
				fields ["id"]			  = {"ecudocsField":"id", "codebinField":"iddtai", "value":""}
				fields ["numero"]		  = {"ecudocsField":"numero", "codebinField":"no", "value":""}
				fields ["fecha_creacion"] = {"ecudocsField":"fecha_creacion", "codebinField":"dtaifechac", "value":""}
				fields ["referencia"]	  = {"ecudocsField": "referencia", "codebinField":"ref", "value":""}

			return fields
		except: 
			raise Exception ("Obteniendo campos de CODEBIN")
			Utils.printException ()

	#------------------------------------------------------
	# Get waitdriver (Open browser)
	#------------------------------------------------------
	@staticmethod
	def getWaitWebdriver (DEBUG=False):
		Utils.printx ("Getting webdriver...")
		if DEBUG:
			BotMigration.webdriver = None

		while not hasattr (BotMigration, "webdriver"):
			Utils.printx ("...Loading webdriver...")
			options = Options()

			#-- For chrome
			#options.add_argument(f"user-agent={user_agent}")
			#service = Service (ChromeDriverManager().install())
			#BotMigration.webdriver = webdriver.Chrome (service=service, options=options)
			#BotMigration.webdriver = webdriver.Chrome ()
			
			#-- For firefox
			#options.add_argument("--headless")
			#GECKOPATH = "/home/lg/.local/bin/geckodriver"
			#GECKOPATH = "./geckodriver"
			#service = Service(executable_path=GECKOPATH)
			#BotMigration.webdriver = webdriver.Firefox (service=service, options=options)
			BotMigration.webdriver = webdriver.Firefox (options=options)

			# Initialize Firefox WebDriver service
			#service = Service(GeckoDriverManager().install())
			#BotMigration.webdriver = webdriver.Firefox(service=service, options=options)
			Utils.printx ("...Webdriver Loaded")


		return BotMigration.webdriver

	#-------------------------------------------------------------------
	# Returns the web driver after login into CODEBIN
	#-------------------------------------------------------------------
	def loginCodebin (self, pais):
		pais = pais.lower ()
		print (f"+++ CODEBIN: ...AutenticAndose con paIs : '{pais}'")
		# Login Form : fill user / password
		loginForm = self.webdriver.find_element (By.TAG_NAME, "form")
		userInput = loginForm.find_element (By.NAME, "user")
		#userInput.send_keys ("GRUPO BYZA")
		userInput.send_keys (self.usuario)
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

	#-------------------------------------------------------------------
	# Return settings for acceding to CODEBIN by "empresa"
	#-------------------------------------------------------------------
	def getCodebinSettingsForEmpresa (self):
		settings = {}
		prefix = None
		if self.empresa == "BYZA":
			prefix = "byza"
			settings ["COLOMBIA"] = {"user":"GRUPO BYZA", "password":"GrupoByza2020*"}
			settings ["ECUADOR"]  = {"user":"GRUPO BYZA", "password":"GrupoByza2020*"}
			settings ["PERU"]	  = {"user":"", "password":"*"}
		elif self.empresa == "NTA":
			prefix = "nta"
			settings ["COLOMBIA"] = {"user":"MARCELA", "password":"NTAIPIALES2023"}
			settings ["ECUADOR"]  = {"user":"KARLA", "password":"NTAIPIALES2023"}
			settings ["PERU"]	  = {"user":"CARLOS", "password":"NTAHUAQUILLAS"}
		elif self.empresa == "LOGITRANS":
			prefix = "logitrans"
			settings ["COLOMBIA"] = {"user":"LUIS FERNANDO", "password":"LuisLogitrans"}
			settings ["ECUADOR"]  = {"user":"PATO", "password":"Patologitrans"}
			settings ["PERU"]	  = {"user":"", "password":""}
		else:
			raise Exception ("Empresa desconocida")
		
		settings ["urlCodebin"] = f"https://{prefix}.corebd.net"
		if self.docType == "CARTAPORTE":
			settings ["link"]	 = f"https://{prefix}.corebd.net/1.cpi/nuevo.cpi.php?modo=3&idunico=%s"
			settings ["menu"]	 = "Carta Porte I"
			settings ["submenu"] = "1.cpi/lista.cpi.php?todos=todos"
			settings ["docPrefix"]	= "CPI"

		elif self.docType == "MANIFIESTO":
			settings ["link"]	 = f"https://{prefix}.corebd.net/2.mci/nuevo.mci.php?modo=3&idunico=%s"
			settings ["menu"]	 = "Manifiesto de Carga"
			settings ["submenu"] = "2.mci/lista.mci.php?todos=todos"
			settings ["docPrefix"]	= "MCI"

		elif self.docType == "DECLARACION":
			settings ["link"]	 = f"https://{prefix}.corebd.net/3.dtai/nuevo.dtai.php?modo=3&idunico=%s"
			settings ["menu"]	 = "Declaración de Transito"
			settings ["submenu"] = "3.dtai/lista.dtai.php?todos=todos"
			settings ["docPrefix"]	= "DTI"
		else:
			print ("Tipo de documento no soportado:", self.docType)
		return settings

	#-------------------------------------------------------------------
	# Add info (permiso) according to "empresa"
	#-------------------------------------------------------------------
	def addInfoEmpresa (self, empresa, formFields):
		infoEmpresa = EcuData.empresas ["BYZA"]
		print (infoEmpresa)
		if empresa == "BYZA" and self.docType == "MANIFIESTO":
			formFields ["txt02"] = infoEmpresa ["permisos"]["originario"]
			formFields ["txt03"] = infoEmpresa ["permisos"]["servicios1"]
		return formFields
	#-------------------------------------------------------------------
	# Save form fields from Ecuapass document to DB
	#-------------------------------------------------------------------
	def saveNewDocToDB (self, formFields, docType, pais, usuario):
		docModel, formModel = Scripts.saveNewDocToDB (formFields, docType, pais, usuario)
		if (docType == "CARTAPORTE"):
			docModel.remitente     = Scripts.getSaveClienteInstance ("txt02", formFields)
			docModel.destinatario  = Scripts.getSaveClienteInstance ("txt03", formFields)
			docModel.fecha_emision = Extractor.getFechaEmisionFromText (formFields ["txt19"])
		elif (docType == "MANIFIESTO"):
			docModel.fecha_emision = Extractor.getFechaEmisionFromText (formFields ["txt40"])
		elif (docType == "DECLARACION"):
			docModel.fecha_emision = Extractor.getFechaEmisionFromText (formFields ["txt23"])
		else:
			raise Exception ("Tipo de Documento Desconocido:", docType)

		docModel.save ()

	#-------------------------------------------------------------------
	#-- Update/Recreate asociations from current documents in DB
	#-------------------------------------------------------------------
	def updateCurrentDBAssociations (self):
		FormModel, DocModel = self.getFormAndDocModels (self.docType)
		documents = DocModel.objects.all ()
		for docModel in documents:
			formModel = docModel.documento
			docFields = self.getDocFieldsFromFormModel (self.docType, formModel)
			docModel.setValues (formModel, docFields, self.pais, self.usuario)
			docModel.save ()

	#-------------------------------------------------------------------
	#-- Return document fields from form Model dict
	#-- {key:{value:XXX, content:XXX}}  <-- {numero:XX, txt00:XX,...,txt24}
	#-------------------------------------------------------------------
	def getDocFieldsFromFormModel (self, docType, formModel):
		formFields = formModel.__dict__
		paramFields = Utils.getParamFieldsForDocument (docType)
		
		docFields = {}
		for key, value in formFields.items():
			try:
				params  = paramFields [key]
				ecudocsField = params ["ecudocsField"]
				docFields [ecudocsField] = {"value": value, "content":value}
			except:
				print (f"Problemas con clave '{key}' obteniendo DocFields")

		return docFields
			
	#-------------------------------------------------------------------
	# Return form document class and register class from document type
	#-------------------------------------------------------------------
	def getFormAndDocModels (self, docType):
		FormModel, DocModel = None, None
		if docType.upper() == "CARTAPORTE":
			FormModel, DocModel = CartaporteForm, Cartaporte
		elif docType.upper() == "MANIFIESTO":
			FormModel, DocModel = ManifiestoForm, Manifiesto
		elif docType.upper() == "DECLARACION":
			FormModel, DocModel = DeclaracionForm, Declaracion 
		else:
			print (f"Error: Tipo de documento '{docType}' no soportado")
			sys.exit (0)

		return FormModel, DocModel

#-------------------------------------------------------------------
# Utils for migration
#-------------------------------------------------------------------
#-- Postgress env vars
def checkDBVars ():
	PGUSER     = os.environ.get ("PGUSER")
	PGPASSWORD = os.environ.get ("PGPASSWORD")
	PGDATABASE = os.environ.get ("PGDATABASE")
	PGHOST     = os.environ.get ("PGHOST")
	PGPORT     = os.environ.get ("PGPORT")

	print ("Postgres DB vars:")
	print ("\t",PGUSER)
	print ("\t",PGPASSWORD)
	print ("\t",PGDATABASE)
	print ("\t",PGHOST)
	print ("\t",PGPORT)
	print ("")

	if input ("Desea continuar (yes/no): ")!="yes":
		return True
	return False

#-------------------------------------------------------------------
#--main
#-------------------------------------------------------------------
main ()
