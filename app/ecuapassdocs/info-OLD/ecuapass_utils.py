import os, json, re, sys, tempfile, datetime, locale

import traceback    # format_exc

from ecuapassdocs.utils.resourceloader import ResourceLoader 
from ecuapassdocs.info.ecuapass_globals import Globals 

def LOG (var):
	# This only works when called directly (not through another function)
	print(f"+++ LOG::{var=}")

#--------------------------------------------------------------------
# Utility function used in EcuBot class
#--------------------------------------------------------------------
class Utils:
	runningDir = None
	message    = ""   # Message sent by 'checkError' function

	#----------------------------------------------------------------
	# For empresas as ALDIA::TRANSERCARGA, ALDIA::SERCARGA
	#----------------------------------------------------------------
	def getEmpresaMatriz (empresa):
		return empresa.split ("::")[0]

	def getEmpresaBranch (empresa):
		return empresa.rsplit ("::")[-1]
	#----------------------------------------------------------------
	# Change Windows newlines (\r\n( to linux newlines (\n)
	#----------------------------------------------------------------
	def convertJsonFieldsNewlinesToWin (jsonFields):
		for key, value in jsonFields.items ():
			if value and type (value) is str:
				jsonFields [key] = value.replace ("\r\n", "\n")
		return jsonFields
			
	#------------------------------------------------------
	#-- Get doc files from dir sorted by number : CO#####, EC#####, PE#####
	#------------------------------------------------------
	def getSortedFilesFromDir (inputDir):
		filesAll = [x for x in os.listdir (inputDir) if ".json" in x]
		dicFiles = {}
		for file in filesAll:
			docNumber = file.split("-")[2][2:]
			dicFiles [docNumber] = file

		sortedFiles = [x[1] for x in sorted (dicFiles.items(), reverse=True)]
		return sortedFiles

	#------------------------------------------------------
	#-- Break text with long lines > maxChars
	#------------------------------------------------------
	def breakLongLinesFromText (text, maxChars):
		def fixText (text, maxChars):
			newLines = []
			try:
				lines = text.split ("\n")
				for line in lines:
					if len (line) > maxChars:
						newLines.append (line [:maxChars])
						newLines.append (line [maxChars:])
					else:
						newLines.append (line)

				return "\n".join (newLines)
			except:
				return text

		#-- Loop until all text lines are fixed
		while True:
			newText = fixText (text, maxChars)
			if newText == text:
				return newText
			text = newText


	#------------------------------------------------------
	#-- Get valid value in vehicle/trailer info
	#------------------------------------------------------
	def isEmptyFormField (text):
		if text == "" or text == None or text.upper().startswith ("X") or text.upper () == "N/A":
			return True
		return False

	
	#------------------------------------------------------
	# Get current date in format: dd-MES-YYYY
	#------------------------------------------------------
#	def getCurrentDate ():
#		locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
#		current_date = datetime.datetime.now()
#		formatted_date = current_date.strftime('%d-%B-%Y')
#		return (formatted_date)

	def getCurrentDate ():
		SPANISH_MONTHS = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
					'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
		# Get current date
		current_date = datetime.datetime.now()

		# Format manually
		day = current_date.day
		month = SPANISH_MONTHS[current_date.month - 1]  # Adjust month index
		year = current_date.year

		formatted_date = f"{day:02d}-{month}-{year}"
		return (formatted_date)


	#------------------------------------------------------
	# Format date string "DD-MM-YYYY" to Postgres "YYYY-MM-DD"
	#------------------------------------------------------
	def formatDateStringToPGDate (date_string):
		if type (date_string) == datetime.datetime:
			date_string = date_string.strftime ("%d-%m-%Y")

		date_object    = datetime.datetime.strptime (date_string, "%d-%m-%Y").date()
		formatted_date = date_object.strftime("%Y-%m-%d")
		return formatted_date

	#------------------------------------------------------
	# Return difference	in days between two dates
	#------------------------------------------------------
	def getDaysDifference (date_str1, date_str2):
		date_format = "%d-%m-%Y"

		try:
			date1 = datetime.datetime.strptime(date_str1, date_format)
			date2 = datetime.datetime.strptime(date_str2, date_format)
			return abs((date2 - date1).days)
		except (ValueError, TypeError):
			return None

	#------------------------------------------------------
	#-- Redirect stdout output to file
	#------------------------------------------------------
	def redirectOutput (logFilename, logFile=None, stdoutOrg=None):
		if logFile == None and stdoutOrg == None:
			logFile    = open (logFilename, "w")
			stdoutOrg  = sys.stdout
			sys.stdout = logFile
		else:
			logFile.close ()
			sys.stdout = stdoutOrg

		return logFile, stdoutOrg

	#------------------------------------------------------
  	#-- Remove text added with confidence value ("wwww||dd")
	#------------------------------------------------------
	def removeConfidenceString (fieldsConfidence):
		fields = {}
		for k in fieldsConfidence:
			confidenceStr = fieldsConfidence [k] 
			fields [k] = confidenceStr.split ("||")[0] if confidenceStr else None
			if fields [k] == "":
				fields [k] = None
		return fields

	
	#------------------------------------------------------
	#-- Get file/files for imageFilename 
	#------------------------------------------------------
	def getPathImage (imageFilename):
		imagesDir = os.path.join (Utils.runningDir, "resources", "images")
		path = os.path.join (imagesDir, imageFilename)
		if os.path.isfile (path):
			return path
		elif os.path.isdir (path):
			pathList = []
			for file in sorted ([os.path.join (path, x) for x in os.listdir (path) if ".png" in x]):
				pathList.append (file)

			return pathList
		else:
			print (f">>> Error: in 'getPathImage' function. Not valid filename or dirname:'{imageFilename}'") 
			return None
			
	#-- Read JSON file
	def readJsonFile (jsonFilepath):
		Utils.printx (f"Leyendo archivo de datos JSON '{jsonFilepath}'...")
		data = json.load (open (jsonFilepath, encoding="utf-8")) 
		return (data)

	#-- Check if 'resultado' has values or is None
	def checkError (resultado, message):
		if resultado == None:
			Utils.message = f"ERROR: '{message}'"
			if "ALERTA" in message:
				Utils.printx (message)
			raise Exception (message)
		return False

	def printx (*args, flush=True, end="\n"):
		print ("SERVER:", *args, flush=flush, end=end)
		message = "SERVER: " + " ".join ([str(x) for x in args])
		return message

	#-- Print exception with added 'message' and 'text'
	#-- If app is EBOT_APP then send it to cloud
	def printException (message, text=None):
		if text:
			Utils.printx ("TEXT:", text) 

		stackTrace = ''.join(traceback.format_exc())
		orgMessage = f"{message}:\n{stackTrace}"
		Utils.printx (orgMessage)

		from ecuapassdocs.info.ecuapass_cloud import EcuCloud 
		EcuCloud.sendLog (Globals.empresa, Globals.version, orgMessage, logType="errors")

	def print_var(var):
		# This only works when called directly (not through another function)
		print(f"{var=}")

	#-- print var and var name
	def log (var):
		import inspect
		frame = inspect.currentframe()
		try:
			# Look through the frame's locals and globals to find the variable name
			for name, value in frame.f_back.f_locals.items():
				if value is var:
					print(f"+++ {name} = {value}")
					break
			else:
				for name, value in frame.f_back.f_globals.items():
					if value is var:
						print(f"{name} = {value}")
						break
				else:
					print("Variable name not found")
		finally:
			del frame # Always clean up the frame reference to avoid reference cycles


	#-- Print var value 	
	def debug (variable, label=None):
		print (f"\n+++ DEBUG: {label}:\n'{variable}'")


	#-- Get value from dict fields [key] 
	def getValue (fields, key):
		try:
			return fields [key]
		except:
			Utils.printException ("EXEPCION: Obteniendo valor para la llave:", key)
			#traceback.print_exception ()

			return None

	#-----------------------------------------------------------
	# Using "search" extracts first group from regular expresion. 
	# Using "findall" extracts last item from regular expresion. 
	#-----------------------------------------------------------
	def getValueRE (RE, text, flags=re.I, function="search"):
		if text != None:
			if function == "search":
				result = re.search (RE, text, flags=flags)
				return result.group() if result else None
			elif function == "findall":
				resultList = re.findall (RE, text, flags=flags)
				return resultList [-1] if resultList else None
		return None

#------------------ MOVED TO EXTRACTOR ------------------------------
#	def getNumber (text):
#		reNumber = r'\d+(?:[.,]?\d*)+' # RE for extracting a float number 
#		number = Utils.getValueRE (reNumber, text, function="findall")
#		return (value_strnumber)


	#-- Save fields dict in JSON 
	def saveFields (fieldsDict, filename, suffixName):
		prefixName	= filename.rsplit (".", 1)[0]
		outFilename = f"{prefixName}-{suffixName}.json"
		with open (outFilename, "w") as fp:
			json.dump (fieldsDict, fp, indent=4, default=str)
		return outFilename

	def initDicToValue (dic, value):
		keys = dic.keys ()
		for k in keys:
			dic [k] = value
		return dic

	#-- Create empty dic from keys
	def createEmptyDic (keys, initialValue=None):
		emptyDic = {}
		for key in keys:
			emptyDic [key] = initialValue
		return emptyDic

	#-- If None return "||LOW"
	def checkLow (data):
		if type (data) == dict:
			for k in data.keys ():
				data [k] = data [k] if data [k] else "||LOW"
		else:
			 data = data if data else "||LOW"

		return data

	#-- Check if any value in data is None or contains "||LOW"
	def anyLowNone (data):
		# Convert to data if single value
		if type (data) != dict:
			data = {"xx" : data}

		if any (value is None or "||LOW" in value for value in data.values()):
			return True

		return False


	#-- Add "||LOW" to value(s) taking into account None
	def addLow (value):
		if type (value) == dict:
			for k in value.keys ():
			 	value [k] = value [k] + "||LOW" if value [k] else "||LOW"
		else:
			value = value + "||LOW" if value else "||LOW"
		return value

		
	#--------------------------------------------------------------------------
	# Converts a number string in American/European format to American-ISO format.
	# Examples:
	# - "24,986.05" (American) → "24986.05"
	# - "13.586,18" (European) → "13586.18"
	# - "1770.00" (American-ISO) → "1770.00"
	# - "1'770.00" (Swiss) → "1770.00"
	#--------------------------------------------------------------------------
	def getISOValue (value):
		if isinstance (value, (int, float)):
			return str(value)
		
		# Remove all non-digit characters except dots and commas
		cleaned = ''.join(c for c in value if c.isdigit() or c in {'.', ','})
		
		# Handle European format (e.g., "1.234,56" → "1234.56")
		if ',' in cleaned and '.' in cleaned:
			# Case: Both separators exist (e.g., "1.234,56")
			if cleaned.index(',') > cleaned.index('.'):
				cleaned = cleaned.replace('.', '').replace(',', '.')
			else: # Edge case: Comma as thousand separator (e.g., "1,234.56")
				cleaned = cleaned.replace(',', '')
		elif ',' in cleaned: # Case: Comma as decimal (European)
			cleaned = cleaned.replace(',', '.')
		
		# Remove any remaining thousands separators (e.g., "1'770" → "1770")
		cleaned = cleaned.replace("'", "").replace(" ", "")
		
		# Ensure it's a valid float (optional validation)
		try:
			if cleaned:
				float (cleaned)
		except ValueError:
			Utils.printException (f"Formato de número inválido: {value}")
			return f"{cleaned}||ERROR"
		
		return cleaned

	#-----------------------------------------------------------
	# Check American number formats and return string value or None
	#-----------------------------------------------------------
	def getFloatValue (value):
		if value == '' or value is None:
			return ''
		try:
			return float (value)
		except ValueError:
			print (f"ERROR: {value}||ERROR")
			return f"{value}||ERROR"

	#---------------------------------------------------------------------------------
	# Validates and converts a European-formatted number (e.g., '3.578,19' or '3601,67') to a float.
    # Returns the float value if valid, otherwise raises a ValueError.	
	#---------------------------------------------------------------------------------
	def euroToFloatValue (value):
		#pattern = r"^\d{1,3}(\.\d{3})*,\d{2}$|^\d+,\d{2}$"  # Allows both formats
		pattern = r"^\d{1,3}(\.\d{3})*(,\d{2})?$|^\d+(,\d{2})?$"  # Allows both integers and decimals
		
		if not re.match(pattern, value):
			print (f"ERROR: Formato númerico Europeo Inválido: {value}")
			return f"{value}||ERROR"

		# Replace thousands separator (.) with nothing and decimal separator (,) with a dot
		normalized_number = value.replace('.', '').replace(',', '.')
		
		return Utils.getFloatValue (normalized_number)

	#---------------------------------------------------------------------------------
	# Validates and converts a European-formatted number (e.g., '3.578,19' or '3601,67') to a float.
    # Returns the float value if valid, otherwise raises a ValueError.	
	#---------------------------------------------------------------------------------
	def americanToFloatValue (value):
		#pattern = r"^\d{1,3}(\.\d{3})*,\d{2}$|^\d+,\d{2}$"  # Allows both formats
		pattern = r"^\d{1,3}(\,\d{3})*(.\d{2})?$|^\d+(.\d{2})?$"  # Allows both integers and decimals
		
		if not re.match(pattern, value):
			print (f"ERROR: Formato númerico Americano Inválido: {value}")
			return f"{value}||ERROR"

		# Replace thousands separator (.) with nothing and decimal separator (,) with a dot
		normalized_number = value.replace(',', '')
		
		return Utils.getFloatValue (normalized_number)

	#-------------- MAYBE OBSOLETE: Replaced by two last ones-----------
	# Convert from Colombian/Ecuadorian values to American values
	#-------------------------------------------------------------------
	def is_valid_colombian_value(value_str):
		# Use regular expression to check if the input value matches the Colombian format
		pattern = re.compile(r'^\d{1,3}(\.\d{3})*(,\d{1,2})?')
		return bool(pattern.match (value_str))

	def is_valid_american_value(value_str):
		# Use regular expression to check if the input value matches the American format
		pattern1 = re.compile(r'^\d{1,3}(,\d{3})*(\.\d{1,2})?$')
		pattern2 = re.compile(r'^\d{3,}(\.\d{1,2})?$')
		return bool (pattern1.match(value_str) or pattern2.match (value_str))

	#-- Requires comma separators for thousands and a period as a decimal separator if present
	def is_strict_american_format (value):
		pattern = r'^\d{1,3}(,\d{3})+(\.\d+)?$'
		locale.setlocale (locale.LC_ALL, 'en_US.UTF-8') # Set the locale to US format for parsing
		if not re.match (pattern, value): # Check if the string matches the strict American format pattern
			return False
		# Try to parse it to ensure it's a valid number in American format
		try:
			locale.atof (value)	# If this works, it's a valid American format number
			return True
		except ValueError:
			return False

	#-- Check if quantity is in american format
	def checkQuantity (value):
		if not value:
			return value
		elif Utils.is_valid_american_value (value):
			return value
		else:
			return f"{value}||ERROR"

	# Convert a float/int value to string american value
	def numberToAmericanFormat (value):
		locale.setlocale (locale.LC_ALL, 'en_US.UTF-8')
		return locale.format_string("%.4f", value, grouping=True)

	# Convert strint in Colombian format to American format
	# 
	def stringToAmericanFormat (value_str):
		value_str = str (value_str)
		if not value_str:
			return ""
		
		#print (">>> Input value str: ", value_str)
		if Utils.is_strict_american_format (value_str):
			return value_str

		# Validate if it is a valid Colombian value
		if value_str and not Utils.is_valid_colombian_value(value_str):
			Utils.printx (f"ALERTA: valores en formato invalido: '{value_str}'")
			return value_str + "||LOW"

		# Replace dots with empty strings
		newValue = ""
		for c in value_str:
			if c.isdigit():
				nc = c
			else:
				nc = "." if c=="," else ","
			newValue += nc
				
		return newValue

	#-- Return string of correct Ecuapass value or "||LOW" e.g. 1500.05
	def getEcuapassFloatValue (ecuapassValue):
		try:
			if ecuapassValue == "" or ecuapassValue == None:
				return 0.0

			if type (ecuapassValue) is float or type (ecuapassValue) is int:
				return float (ecuapassValue)

			else:
				return str (float (ecuapassValue))
		except:
			Utils.printException (f"Error en formato del valor: '{ecuapassValue}'")
			return "||LOW"
	

	#----------------------------------------------------------------
	# Return docs fields ('ecudocsField') from app fields:
	# "codebinField", "aldiaField", "appField"
	#----------------------------------------------------------------
	def getDocFieldsFromAppFields (appFieldsDic, docType, appFieldType):
		docFields    = {}
		paramFields = Utils.getInputsParameters (docType)
		for key, params in paramFields.items ():
			docField =  None
			try:
				docField, appField = params ["ecudocsField"] , params [appFieldType]
				if not docField:
					continue
				if type (appField) is dict:  # Case for "aldiaField" conformed by multiple app fields
					appField = next (iter (appField))
					docFields [docField] = appFieldsDic [appField]
				value = appFieldsDic [appField] if appField else ""
				docFields [docField] = value
			except KeyError as ex:
				Utils.printException (f"Error obteniendo DocField from AppField. Key: '{key}'")

		# Add special app fields to docFields
		for key in appFieldsDic:
			if key.startswith ("app"): # Special app field as MRN in SANCHEZPOLD
				docFields [key] = appFieldsDic [key]

		docFields = Utils.convertJsonFieldsNewlinesToWin (docFields)
		return docFields


	#-------------------------------------------------------------------
	# Return ecudocFields from formFields
	# {01_Remitente:XXX, 02_Destinatario:YYY,...} {txt01:XXXX, txt02:YYY}
	#-------------------------------------------------------------------
	def getDocFieldsFromFormFields (docType, formFields):
		docFields = Utils.getDocFieldsFromAppFields (formFields, docType, "appField") 
		return docFields

	#-------------------------------------------------------------------
	#-- Return input parameters field for document
	#-------------------------------------------------------------------
	def getParamFieldsForDocument (docType):
		inputsParametersFile = Utils.getInputsParametersFile (docType)
		paramFields      = ResourceLoader.loadJson ("docs", inputsParametersFile)
		return paramFields

	#-- Return PDF coordinates fields for empresa, document type
	def getPdfCoordinates (empresa, docType):
		coordsDic = None 
		if empresa == "ALDIA" and docType == "MANIFIESTO":
			coordsDicAll = ResourceLoader.loadJson ("docs", "coordinates_pdfs_docs_ALDIA.json")
			coordsDic = coordsDicAll ["MANIFIESTO"]
		elif empresa == "ALDIA" and docType == "CARTAPORTE":
			coordsDicAll = ResourceLoader.loadJson ("docs", "coordinates_pdfs_docs_ALDIA.json")
			coordsDic = coordsDicAll ["CARTAPORTE"]
		else:
			raise Exception (f"+++ No existen coordenadas PDF para '{empresa}' : '{docType}'")

		return coordsDic

	#-------------------------------------------------------------------
	# Get form fields from migration fields:
	# Form fields {id,numero,txt0a,txt00,txt01,...,txt24}
	# Migration fields {id:{"ecudoc", "codebinField", "value"}}
	#-------------------------------------------------------------------
	def getFormFieldsFromMigrationFieldsFile (migrationFilename):
		formFields = {}

		with open (migrationFilename, encoding="utf-8") as file:
			migrationFields = json.load (file)
		
		# Get form fields
		for key, fields in migrationFields.items():
			formFields [key]   = fields ["value"]
		return formFields

#	#--------------- MOVED TO EDOS>_UTILS ------------------------------
#	#-- Return pair key:values ['value'] from keys in paramsFields (Used in: EDocs)
#	#-------------------------------------------------------------------
#	def getFieldsFromParams (paramsFields):
#		fields = {}
#		for key in paramsFields:
#			fields [key] = paramsFields [key]['value']
#
#		return fields

	def setInputValuesToInputParams (inputValues, inputParams):
		for key in inputValues:
			try:
				inputParams [key]["value"] = inputValues [key]
			except KeyError as ex:
				print (f"Llave '{key}' no encontrada")


		return inputParams
		
	#-------------------------------------------------------------------
	# Get the number (ej. CO00902, EC03455) from the filename
	#-------------------------------------------------------------------
	def getDocumentNumberFromFilename (filename):
		numbers = re.findall (r"\w*\d+", filename)
		docNumber = numbers [-1]
		docNumber = docNumber.replace ("COCO", "CO")
		docNumber = docNumber.replace ("ECEC", "EC")
		docNumber = docNumber.replace ("PEPE", "PE")
		return docNumber

	#-------------------------------------------------------------------
	# Return CARTAPORTE or MANIFIESTO
	#-------------------------------------------------------------------
	#----------------------------------------------------------------
	#-- Get document type from filename
	#----------------------------------------------------------------
	def getDocumentTypeFromFilename (filename):
		docType = os.path.basename (filename).split("-")[0].upper()
		filename = filename.upper ()
		if "CPI" in filename or "CARTAPORTE" in filename:
			return ("CARTAPORTE")
		elif "MCI" in filename or "MANIFIESTO" in filename:
			return ("MANIFIESTO")
		elif "DCL" in filename or "DECLARACION" in filename:
			return ("DECLARACION")
		else:
			raise Exception (f"Tipo de documento desconocido para: '{filename}'")
	
	#-- Return doc prefix from doc type
	def getDocPrefix (docType):
		docPrefixes = {"CARTAPORTE":"CPI", "MANIFIESTO":"MCI", "DECLARACION":"DTI"}
		return docPrefixes [docType]

	#-------------------------------------------------------------------
	# Get 'pais, codigo' from document number or text
	#-------------------------------------------------------------------
	def getPaisCodigoFromDocNumber (docNumber):
		paisCodes = {"COLOMBIA":"CO", "ECUADOR":"EC", "PERU": "PE"}
		pais      = Utils.getPaisFromDocNumber (docNumber)
		codigo    = paisCodes [pais]
		return pais.lower(), codigo

	def getPaisFromDocNumber (docNumber):
		try:
			codePaises = {"CO": "COLOMBIA", "EC": "ECUADOR", "PE": "PERU"}
			code   = Utils.getCodigoPais (docNumber)
			pais   = codePaises [code]
			return pais
		except:
			print (f"ALERTA: No se pudo determinar código del pais desde el número: '{docNumber}'")

	#-- Returns the first two letters from document number
	def getCodigoPais (docNumber):
		docNumber = docNumber.upper ()
		try:
			if docNumber.startswith ("CO"): 
				return "CO"
			elif docNumber.startswith ("EC"): 
				return "EC"
			elif docNumber.startswith ("PE"): 
				return "PE"
		except:
			print (f"ALERTA: No se pudo determinar código del pais desde el número: '{docNumber}'")
		return ""
	#-------------------------------------------------------------------
	# Get 'pais, codigo' from text
	#-------------------------------------------------------------------
	def getPaisCodigoFromText (self, text):
		pais, codigo = "NONE", "NO" 
		text = text.upper ()

		if "COLOMBIA" in text:
			pais, codigo = "colombia", "CO"
		elif "ECUADOR" in text:
			pais, codigo = "ecuador", "EC"
		elif "PERU" in text:
			pais, codigo = "peru", "PE"
		else:
			raise Exception (f"No se encontró país en texto: '{text}'")

		return pais, codigo

	#----------------------------------------------------------------
	# Used in EcuapassDocs web
	#----------------------------------------------------------------
	def getCodigoPaisFromPais (pais): #"COLOMBIA", "ECUADOR", "PERU"
		try:
			paises   = {"COLOMBIA":"CO", "ECUADOR":"EC", "PERU":"PE"}
			return paises [pais.upper()]
		except:
			Utils.printException (f"Pais desconocido: '{pais}'") 
			return None

	def getPaisFromCodigoPais (paisCode):
		try:
			paisesCodes   = {"CO":"COLOMBIA", "EC":"ECUADOR", "PE":"PERU"}
			return paisesCodes [paisCode.upper()]
		except:
			Utils.printException (f"Codigo Pais desconocido: '{paisCode}'") 
			return None

	#-------------------------------------------------------------------
	# Get the number part from document number (e.g. COXXXX -> XXXX)
	#-------------------------------------------------------------------
	def getNumberFromDocNumber (docNumber):
		pattern = r'^(CO|EC|PE)(\d+)$'

		match = re.match (pattern, docNumber)
		if match:
			number = match.group(2)
			return int (number)
		else:
			raise Exception (f"Número de documento '{docNumber}' sin país")

	#-------------------------------------------------------------------
	# Return 'EXPORTACION' or 'IMPORTACION' according to 'pais' and 'empresa'
	# Used in EcuapassDocs web
	#-------------------------------------------------------------------
	def getProcedimientoFromPais (empresa, pais):
		procedimientosBYZA = {"CO":"IMPORTACION", "EC":"EXPORTACION", "PE":"EXPORTACION"}
		pais = pais.upper ()
		if empresa == "BYZA" and pais.startswith ("CO"):
			return "IMPORTACION"
		elif empresa == "BYZA" and pais.startswith ("EC"):
			return "EXPORTACION"
		else:
			raise Exception (f"No se pudo identificar procedimiento desde '{empresa}':'{pais}'")

	#----------------------------------------------------------------
	#-- Return fiels:values of input parameters 
	#----------------------------------------------------------------
	def getInputsParameters (docType):
		inputsParametersFile = Utils.getInputsParametersFile (docType)
		inputsParameters = ResourceLoader.loadJson ("docs", inputsParametersFile)
		return inputsParameters

	#-- Return parameters file for docType
	def getInputsParametersFile (docType):
		if docType == "CARTAPORTE":
			inputsParametersFile = "input_parameters_cartaporte.json"
		elif docType == "MANIFIESTO":
			inputsParametersFile = "input_parameters_manifiesto.json"
		elif docType == "DECLARACION":
			inputsParametersFile = "input_parameters_declaracion.json"
		else:
			raise Exception (f"Tipo de documento desconocido:", docType)
		return inputsParametersFile


	#-----------------------------------------------------------
	# Load user settings (empresa, codebinUrl, codebinUser...)
	#-----------------------------------------------------------
	def loadSettings (runningDir):
		settingsPath  = os.path.join (runningDir, "settings.txt")
		if os.path.exists (settingsPath) == False:
			Utils.printx (f"ALERTA: El archivo de configuración '{settingsPath}' no existe")
			sys.exit (-1)

		settings  = json.load (open (settingsPath, encoding="utf-8")) 

		empresa   = settings ["empresa"]
		Utils.printx ("Empresa actual: ", empresa)
		return settings

	#-----------------------------------------------------------
	# Get ecuField value obtained from docFields
	# CLIENTS: DocsWeb for saving entities, dates,...
	#-----------------------------------------------------------
	def getEcuapassFieldInfo (INFOCLASS, ecuFieldKey, docFields):
		docFieldsPath, runningDir = Utils.createTemporalJson (docFields)
		docInfo           = INFOCLASS (docFieldsPath, runningDir)
		ecuapassFields    = docInfo.extractEcuapassFields ()
		ecuapassFields    = Utils.removeConfidenceString (ecuapassFields)
		fieldInfo         = ecuapassFields [ecuFieldKey]
		return fieldInfo

	def createTemporalJson (docFields):
		numero   = docFields ["00_Numero"]
		tmpPath        = tempfile.gettempdir ()
		tmpPath = os.path.abspath(tmpPath)

		docFieldsPath = os.path.join (tmpPath, f"ECUDOC-{numero}.json")
		json.dump (docFields, open (docFieldsPath, "w"))
		return (docFieldsPath, tmpPath)

	#-----------------------------------------------------------
	# Return a string
	#-----------------------------------------------------------
	def toString (value):
		if not value:
			return ""
		elif type (value) is list or type (value) is tuple:
			return [str (x) for x in value]
		else:
			return str (value)



