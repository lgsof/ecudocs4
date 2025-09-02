import re, os
from importlib import resources
from traceback import format_exc as traceback_format_exc

from .ecuapass_utils import Utils
from .resourceloader import ResourceLoader 

text = \
"NATIONAL OILWELL VARCO DE COLOMBIA NIT 8001563544\n\
CALLE98NO9A21PISO4\n\
BOGOTA - COLOMBIA"

def main ():
	subject = Utils.createEmptyDic (["nombre","direccion","pais","ciudad","tipoId","numeroId"])
	print (f"+++\n\n INPUT TEXT:\n'{text}'")
	outText, subject = Extractor.removeSubjectId (text, subject, "Subject")
	print (f"+++\nOUTPUT TEXT:\n'{outText}'")
	print (f"+++\nSUBJECT:\n'{subject}'")
	
		
#--------------------------------------------------------------------
# Class for extracting different values from document texts
#--------------------------------------------------------------------
class Extractor:
	#-- Remove "||LOW" sufix
	def delLow (text):
		if text == None: 
			return text

		return str(text).replace ("||LOW", "")
	#-------------------------------------------------------------------
	#-- Get location info: ciudad, pais, fecha -------------------------
	#-- Boxes: Recepcion, Embarque, Entrega ----------------------------
	#-------------------------------------------------------------------
	def extractLocationDate (text, resourcesPath, fieldType=None):
		location = {"ciudad":"||LOW", "pais":"||LOW", "fecha":"||LOW"}
		try:
			text   = text.replace ("\n", " ")
			# Fecha
			fecha = Extractor.getDate (text, resourcesPath)
			location ["fecha"] = fecha if fecha else "||LOW"
			# Pais
			text, location = Extractor.removeSubjectCiudadPais (text, location, resourcesPath, fieldType)
		except:
			Utils.printException (f"Obteniendo datos de la localización: '{fieldType}' en el texto", text)

		return (location)

	#-----------------------------------------------------------
	#-- Get subject (remitente, destinatario, declarante,..) info
	#-- Info: nombre, dir, pais, ciudad, id, idNro
	#-----------------------------------------------------------
	def getSubjectInfoFromText (text, resourcesPath, subjectType):
		subject = {"nombre":None, "direccion":None, "pais": None, 
		           "ciudad":None, "tipoId":None, "numeroId": None}
		try:
			lines   = text.split ("\n")

			if len (lines) == 3:
				nameDirLines = lines [0:2]
				idPaisLine   = lines [2]
			elif len (lines) == 4:
				nameDirLines = lines [0:3]
				idPaisLine   = lines [3]
			elif len (lines) < 3:
				print (f">>> Alerta:  Pocas líneas de texto para extraer información de empresa.")
				return subject

			text, subject = Extractor.removeSubjectId (idPaisLine, subject, subjectType)
			text, subject = Extractor.removeSubjectCiudadPais (text, subject, resourcesPath, subjectType)
			nameDirText   = "\n".join (nameDirLines)
			text, subject = Extractor.removeSubjectNombreDireccion (nameDirText, subject, subjectType)
			#subject ["numeroId"] = Utils.convertToEcuapassId (subject ["numeroId"])
		except:
			Utils.printException (f"Obteniendo datos del sujeto: '{subjectType}' en el texto: '{text}'")

		print (subject)
		return (subject)

	#-- Extracts and replaces IdType and IdNumber from text-------
	#-- "RUC: 0990017212001", "RUC N. 0993045462001"
	def getReplaceSubjectId (text, subject, replaceString, type):
		try:
			if not any (x in text.upper() for x in ["NIT", "RUC", "OTROS","ID"]): 
				return (text, subject)

			reNumber = r'\d+(?:[.,]*\d*)+' # RE for extracting a float number 
			#reId     = rf"(RUC|NIT|OTROS|ID)[\s.:]+({reNumber}(?:-\d)?)[ ]*"
			reId     = rf"(RUC|NIT|OTROS|ID)(?:[\s.:]+|[N.\s*])*({reNumber}(?:-\d)?)[ ]*"
			result	 = re.search (reId, text, flags=re.S)
		 
			subject ["tipoId"]   = result.group (1) if result else None
			subject ["numeroId"] = result.group (2).replace (".", "") if result else None

			#text	 = re.sub (reId, replaceString, text, flags=re.S).strip()
			text	 = re.sub (reId, replaceString, text, flags=re.S)
			print (f"+++ replaced text '{text}'")
		except:
			Utils.printException (f"Obteniendo informacion de ID de '{type}'")

		return (text, subject)

	#--  Extracts and removes IdType and IdNumber from text-------
	def removeSubjectId (text, subject, type):
		text, subject = Extractor.getReplaceSubjectId (text, subject, "", type)
		return (text, subject)
		
	def getSubjectId (text):
		resultsDic = {"tipoId":None, "numeroId":None}
		outText, resultsDic = Extractor.removeSubjectId (text, resultsDic, "Subject")
		return resultsDic ["numeroId"]

	def getIdInfo (text):
		resultsDic = {"tipoId":None, "numeroId":None}
		outText, resultsDic = Extractor.removeSubjectId (text, resultsDic, "Subject")
		return resultsDic


	#-- Get ciudad + pais using data from ecuapass ------------------
	def removeSubjectCiudadPais (text, subject, resourcesPath, type):
		text = text.upper ()
		try:
			rePais = ".*?(ECUADOR|COLOMBIA|PERU|VENEZUELA)"
			pais   = Extractor.getValueRE (rePais, text, re.I)
			subject ["pais"] = pais
				
			cities = Extractor.getSubjectCitiesString (pais, resourcesPath)

			reLocation = rf"(?P<ciudad>{cities})[\s\-,\s]+(?P<pais>{pais})[.\s]*"
			result = re.search (reLocation, text, flags=re.I)
			if (result == None):
				printx (f"Ciudad desconocida en texto: '{text}' de '{type}'")
			else:
				subject ["ciudad"] = result.group ("ciudad") if result else None
				text	= text.replace (result.group (0), "")

		except:
			Utils.printException (f"Obteniendo ciudad-pais de '{type}'", text)

		return (text.strip(), subject)

	#-- Extracts and remove Nombre and Direccion---------------------
	#-- Check if name or dir is expanded in more than one line ------
	def removeSubjectNombreDireccion (text, subject, type):
		try:
			lines = text.split ("\n")
			if len (lines) == 2:
				subject ["nombre"]    = lines [0].strip()
				subject ["direccion"] = lines [1].strip()
			elif len (lines) == 3:
				if len (lines [0]) > len (lines [1]):
					subject ["nombre"]    = lines [0].strip () + " " + lines [1].strip () + "||LOW"
					subject ["direccion"] = lines [2].strip () + "||LOW"
				else: 
					subject ["nombre"]    = lines [0].strip () + "||LOW"
					subject ["direccion"] = lines [1].strip () + " " + lines [2].strip () + "||LOW"
		except:
			Utils.printException (f"Obteniendo nombre-direccion de '{type}'")

		return (text, subject)

	#-- Assuming nombre is always in the first line
	def getSubjectNombre (text):
		nombre = text.split("\n")[0]
		return nombre

	#-----------------------------------------------------------
	# Return None if value is not valid, for default values or dicts
	#-----------------------------------------------------------
	def getValidValue (value):
		try:
			if type (value) is not dict:
				return value if Extractor.isValidValue (value) else None
			else:
				numInvalids = len ([v for k,v in value.items () if not Extractor.isValidValue (v)])
				return value if numInvalids < 2 else None
		except:
			Utils.printException (f"Obteniendo valor válido desde valor '{value}'")
			return None

	#-- Check if text contains word or it is not None or empty
	def isValidValue (text):
		reXXX =  r'^(X+\s?)+$'  # 'X' 'XXX' 'X X X'
		if text is None or text.strip() == "":
			return False
		elif re.fullmatch (reXXX, text):
			return False
		elif any ([text.upper().strip() == x for x in ["", "S/N", "N/A"]]):
			return False

		# Count the number of alphanumeric characters
		alnum_count = len(re.findall(r'[a-zA-Z0-9]', text))
		return alnum_count > 1 		

	#-----------------------------------------------------------
	# Using "search" extracts first group from regular expresion. 
	# Using "findall" extracts last item from regular expresion. 
	#-----------------------------------------------------------
	def getValueRE (RE, text, flags=re.I, function="search"):
		if text != None:
			if function == "search":
				result = re.search (RE, text, flags=flags)
				return result.group (1) if result else None
			elif function == "findall":
				resultList = re.findall (RE, text, flags=flags)
				return resultList [-1] if resultList else None
		return None

	#-- Extract all type of number (int, float..) -------------------
	def getNumber (text, FIRST=True):
		reNumber = r'\d+(?:[.,]?\d*)+' # RE for extracting a float number 
		if FIRST:
			number = Utils.getValueRE (reNumber, text, function="search")
		else:
			number = Utils.getValueRE (reNumber, text, function="findall")
		return (number)

	def getRemoveNumber (text, FIRST=True):
		number = Extractor.getNumber (text, FIRST)
		if number != None:
			text.replace (number, "")
		return text, number

	#-- Get "numero documento" with possible prefix "No."------------
	def getNumeroDocumento (text):
		# Cases SILOGISTICA and others
		# Examples: ["N° PO-CO-0011-21-338781-23", "No.019387", "CO003627"]
		reNumber = r'(?:No\.\s*)?([A-Za-z0-9]+)'
		reNumber = r'(?:N.*?)?\b([A-Za-z0-9-]+)\b'

		# NTA, BYZA, SYTSA
		#reNumber = r'([A-Za-z]+\d+)'
		number   = Extractor.getValueRE (reNumber, text)
		return number
	
	#-- Get MRN number from text using the pattern "CECXXXX"
	def getMRNFromText (text):
		reMRN = r'(?:MRN:?\s+)?(CEC[-\d]+)'
		mrn_match = re.search (reMRN, text)  # Searches for the first occurrence

		return mrn_match.group (1) if mrn_match else None

	def getLastString (text):
		string = None
		try:
			reStrings = r'([a-zA-Z0-9-]+)'
			results   = re.findall (reStrings, text) 

			if len (results) > 1:
				string    = results [-1] if results else None 
		except Exception as e:
			Utils.printException (f"Extrayendo última cadena desde el texto: '{text}'", e)
		return string

	def getFirstString (text):
		string = None
		try:
			reStrings = r'([a-zA-Z0-9-]+)'
			results   = re.findall (reStrings, text) 
			string    = results [0] if results else None 
		except Exception as e:
			Utils.printException (f"Extrayendo última cadena desde el texto: '{text}'", e)
		return string
	
	#-- Return items separated by ',' within a text separated by symbols like:',', '-', '/', ...
	def getItemsFromTextList (text):
		reItems = r'\W+'
		items   = re.split (r'\W+', text.strip())
		return ",".join (items) if items else None

	#------------------------------------------------------------------
	# Extracts last word from a string with 1 or more words|numbers
	#------------------------------------------------------------------
	def getLastWord (text):
		word = None
		try:
			# RE for extracting all words as a list (using findall)
			reWords = r'\b[A-Za-z]+(?:/\w+)?\b' 
			results = re.findall (reWords, text) 
			word    = results [-1] if results else None 
		except Exception as e:
			Utils.printException (f"Extrayendo última palabra desde el texto: '{text}'", e)
		return word
	
	#------------------------------------------------------------------
	# Extracts last int number from a string with 1 or more numbers
	#------------------------------------------------------------------
	def getLastNumber (text):
		number = None
		try:
			reNumbers = r'\b\d+\b' # RE for extracting all numeric values as a list (using findall)
			number = re.findall (reNumbers, text)[-1]
		except:
			Utils.printException ("Extrayendo último número desde el texto: ", text)
		return number
	#------------------------------------------------------------------
	# Extract conductor's name (full)
	#------------------------------------------------------------------
	def extractNames (text):
		names = None
		try:
			#reNames = r'\b[A-Z][A-Za-z\s]+\b'
			reNames = r'\b[A-ZÁÉÍÓÚÜÑ][A-Za-záéíóúüñÁÉÍÓÚÜÑ\s]+\b'
			names = re.search (reNames, text).group(0).strip()
		except:
			Utils.printException ("Extrayendo nombres desde el texto: ", text)
		return names
			
	#------------------------------------------------------------------
	# Get pais from nacionality 
	#------------------------------------------------------------------
	def getPaisFromPrefix (text):
		pais = None
		try:
			if "COL" in text.upper():
				pais = "COLOMBIA"	
			elif "ECU" in text.upper():
				pais = "ECUADOR"	
			elif "PER" in text.upper():
				pais = "PERU"	
		except:
			Utils.printException ("Obtenidendo pais desde nacionalidad en el texto:", text)
		return pais

	#------------------------------------------------------------------
	# Extract pais
	#------------------------------------------------------------------
	def getPais (text, resourcesPath):
		try:
			rePaises = Extractor.getDataString ("paises.txt", resourcesPath)
			pais     = Extractor.getValueRE (f"({rePaises})", text, re.I)

			if not pais: # try "(CO), "(EC)" and "(PE)"
				rePais   = r'.*\((CO|EC|PE)\)'
				paisCode = Extractor.getValueRE (rePais, text, re.I)
				if paisCode:
					pais     = Utils.getPaisFromCodigoPais (paisCode)
			return pais
		except:
			Utils.printException (f"Obteniendo pais desde texto '{text}'")
			return 

	def getPaisAndino (text):
		pais = ""
		try:
			rePais   = r'\b(COLOMBIA|ECUADOR|PERU)\b'
			match    = re.search (rePais, text, re.I)
			pais     = match.group (0).upper ()
		except:
			Utils.printException (f"Obteniendo pais andino desde texto: '{text}'")
		return pais if pais else ""

		

	#-- Get ciudad given pais else return stripped string ------------ 
	def getCiudad (text, pais, resourcesPath, ECUAPASS=True):
		ciudad = None
		try:
			if pais or ECUAPASS: # if pais get ciudades from pais and search them in text
				reCities = Extractor.getSubjectCitiesString (pais, resourcesPath)
				ciudad   = Extractor.getValueRE (f"({reCities})", text, re.I)
			else:      # if no pais, get the substring without trailing spaces
				reCiudad = r"\b(\w+(?:\s+\w+)*)\b"
				results  = re.findall (reCiudad, text)
				ciudad   = results [-1] if results [-1] else None
		except:
			Utils.printException (f"Obteniendo ciudad desde texto: '{text}'")
		return ciudad if ciudad else ""


	#-- Get ciudad-pais comparing or not with ciudades in ECUAPASS
	def getCiudadPais (text, resourcesPath, ECUAPASS=True):
		ciudad, pais = "", ""
		try:
			print (f"+++ getCiudadPais: text '{text}'")
			if ECUAPASS:
				pais   = Extractor.getPais (text, resourcesPath)
				print (f"+++ pais '{pais}'")
				ciudad = Extractor.getCiudad (text, pais, resourcesPath)
				print (f"+++ ciudad '{ciudad}'")
			else:
				reCiudadPais = r"(?i)(\b[\w\s]+?)\s*-\s*(COLOMBIA|ECUADOR|PERU)\b"
				match = re.search (reCiudadPais, text)
				if match:
					ciudad = match.group(1).strip()
					pais   = match.group(2)
		except:
			print (f"+++ Extracción Ciudad-Pais incompleta desde el texto '{text}'")

		return ciudad, pais

	def getCiudadNoPais (text):
		try:
			pattern = r'^\s*(?P<city>[^\-]+?)\s*(?:-\s*(?P<country>COLOMBIA|ECUADOR|PERU)\s*)?$'
			match = re.match (pattern, text, re.IGNORECASE)
			if match:
				city = match.group("city").strip()
				country = match.group("country").upper() if match.group("country") else None
				return city, country
		except:
			Utils.printException (f"(Obteniendo ciudad - [pais] from text: '{text}'")
		return None, None


	#------------------------------------------------------------------
	# Extract 'placa' and 'pais'
	#------------------------------------------------------------------
	def getPlacaPais (text, resourcesPath):
		result = {"placa":None, "pais":None}

		text = Extractor.getValidValue (text)
		if not text:
			return result

		try:
			pais             = Extractor.getPais (text, resourcesPath)
			if pais:
				text         = text.replace (pais, "")   
			#rePlacaPais01 = r"(\w+)\W+(\w+)"
			#rePlacaPais      = r'^([A-Z0-9]+)[\s\-]*?(COLOMBIA|ECUADOR|PERU).*$'
			rePlaca           = r'(\b[A-Z0-9]+[\s]*[A-Z0-9]+\b)'
			result ["placa"]  = Extractor.getValueRE (rePlaca, text).replace (" ","")
			result ["pais"]   = pais
		except:
			Utils.printException (f"Extrayendo placa pais desde el texto: '{text}'")
		return result
			
    
	#-- Get placa from text with Placa-Pais
	def getPlaca (text):
		placa = None
		text = Extractor.getValidValue (text)
		if not text:
			return result

		try:
			rePlaca           = r'(\b[A-Z0-9]+[\s\-]*[A-Z0-9]+\b)[\s\-]*?(COLOMBIA|ECUADOR|PERU).*$'
			placa             = Extractor.getValueRE (rePlaca, text)
			placa             = placa.replace (" ","").replace("-","")
		except:
			Utils.printException (f"Extrayendo placa pais desde el texto: '{text}'")
		return placa

	#-- Extract chassis number (assuming it's alphanumeric, 17 characters long)
	def getVehiculoChasis (text):
		reChasis = r"([A-HJ-NPR-Z0-9]{17})"
		chasis = Extractor.getValueRE (reChasis, text)
		if not chasis:
			chasis = Extractor.getValidValue (text) 
		return chasis if chasis else '||LOW'

	#------------------------------------------------------------------
	# Get 'embalaje' from text with number + embalaje: NNN WWWWW
	# For BOT: numbers. For PREDITION: literals
	#------------------------------------------------------------------
	def getTipoEmbalaje (text, analysisType="BOT"):
		try:
			embalaje   = Extractor.getLastWord (text)
			if analysisType == "BOT":  # For BOT: numbers. For PREDITION: literals
				embalaje = Extractor.getCodeEmbalaje (embalaje)
			return embalaje
		except:
			Utils.printx (f"Problemas extrayendo embalaje desde texto: '{text}'")
			return None

	#-- Return the ECUAPASS code for embalaje name
	def getCodeEmbalaje (embalaje):
		if "PALLET" in embalaje or "ESTIBA" in embalaje:
			return "152" # "[152] PALETAS"
		elif "SACO" in embalaje.upper ():
			return "104" # "[104] SACO"
		elif "CAJA" in embalaje.upper ():
			return "035" # "[035] CAJA"
		else:
			return embalaje.strip () + "||LOW"

	
	#-- Return ECUAPASS code for deposito name
	def getCodeDeposito (deposito, resourcesPath):
		print (f"+++ Extractor runningDir  '{os.getcwd()}'")
		depositosDic = Extractor.getDataDic ("depositos_tulcan.txt", resourcesPath)
		print (f"+++ Extractor depositosDoc  '{depositosDic}'")
		for id in depositosDic:
			if deposito in depositosDic [id]:
				return id
		return None

	#------------------------------------------------------------------
	#-- Extract numerical or text date from text ----------------------
	#------------------------------------------------------------------
	def getFechaEmisionFromText (text):
		try:
			fecha        = Extractor.getDate (text)
			fechaEmision = Utils.formatDateStringToPGDate (fecha)
			return fechaEmision
		except:
			Utils.printException ("Error obteniendo fecha desde texto:", f"'{text}'")
			return None

	def getDate (text, resourcesPath=None):
		numericalDate = "||LOW"
		try:
			print (f"\n+++ getDate text '{text}'")
			# Load months from data file
			monthsString = "ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE"
			monthsStringShort = "ENE.|FEB.|MAR.|ABR.|MAY.|JUN.|JUL.|AGO.|SEP.|OCT.|NOV.|DIC."
			monthsList   = [m [:3] for m in monthsString.split ("|")]  # First three letters
		
			# Search for numerical or text date
			reDay      = r'(?P<day>\d{1,2})'
			reMonthNum = r'(?P<month>\d{1,2})'
			#reMonthTxt = rf'(?P<month>{monthsStringShort})'
			reMonthTxt = rf'(?P<month>{monthsStringShort}|{monthsString})'
			reYear     = r'(?P<year>\d[.]?\d{3})'
			reWordSep  = r'(?:\s+(?:DE|DEL))*\s*'
			reSep      = r'(-|/)'

			reDate0 = rf'\b{reDay}\s*{reSep}\s*{reMonthNum}\s*{reSep}\s*{reYear}\b'     # 31-12-2023
			reDate1 = rf'\b{reYear}{reSep}{reMonthNum}{reSep}{reDay}\b'         # 2023/12/31

			reDate2 = rf'\b{reMonthTxt}\s+{reDay}{reWordSep}{reYear}\b'         # Junio 20 del 2023
			reDate3 = rf'\b{reMonthTxt}\s+{reDay}{reSep}{reYear}\b'             # Junio 20/2023
			# 28 DE ENERO DE 2025
			reDate4 = rf'\b{reDay}{reWordSep}{reMonthTxt}{reWordSep}{reYear}\b' # 20 de Junio del 2023
			reDate5 = rf'\b{reYear}{reSep}{reMonthTxt}{reSep}{reDay}\b'         # 2023/DICIEMBRE/31
			reDate6 = rf'\b{reDay}{reSep}{reMonthTxt}{reSep}{reYear}\b'         # 31/DICIEMBRE/2023
			reDateOptions = [reDate0, reDate1, reDate2, reDate3, reDate4, reDate5, reDate6]

			# Evaluate all reDates and select the one with results
			for (option, reDate) in enumerate (reDateOptions):
				result = re.search (reDate, text, re.I)
				if result:
					break

			if not result:
				printx (f"No existe fecha en texto '{text}'")
				return None

			month = result.group('month')
			if option > 1:
				month  = monthsList.index (month.upper()[:3]) + 1     # First three letters

			year          = result.group ('year').replace (".", "")
			numericalDate = f"{result.group('day')}-{str (month).zfill(2)}-{year}"
			print (f"+++ getDate results: '{numericalDate}'")
		except Exception as e:
			Utils.printException (f"Obteniendo fecha desde texto: '{text}'", e)
			
		return numericalDate

	#-------------------------------------------------------------------
	#-- Load cities from DB and create a piped string of cites ---------
	#-------------------------------------------------------------------
	def getSubjectCitiesString (pais, resourcesPath):
		if pais in ["COLOMBIA","ECUADOR","PERU","VENEZUELA"]:
			ciudadesFile = f"ciudades_{pais.lower()}.txt"
			citiesString = Extractor.getDataString (ciudadesFile, resourcesPath)
		else:
			return None

		return citiesString

	#-------------------------------------------------------------------
	#-- Get ECUAPASS data items as dic taking resources from package no path
	#-------------------------------------------------------------------
	def getDataDic (dataFilename, resourcesPath, From="values"):
		dataPath        = os.path.join (resourcesPath, dataFilename)
		dirList         = dataPath.split (os.path.sep)
		resourceName    = dirList [-1]
		resourcePackage = dirList [-2]

		dataDic = {} 
		dataLines = ResourceLoader.loadText (resourcePackage, resourceName)

		for line in dataLines [1:]:
			res = re.search (r"\[(.+)\]\s+(.+)", line)
			dataDic [res.group(1)] = res.group(2)

		return (dataDic)
  
	#-------------------------------------------------------------------
	#-- Return a piped string of ECUPASS data used in regular expression
	#-- From join "values" or join "keys"
	#-------------------------------------------------------------------
	def getDataString (dataFilename, resourcesPath, From="values"):
		dataPath   = os.path.join (resourcesPath, dataFilename)
		dataDic    = Extractor.getDataDic (dataFilename, resourcesPath)
		dataString = None
		if From=="values":
			#dataString = "|".join (map (re.escape, dataDic.values())) #e.g. 'New York' to 'New\\ York'
			dataString = "|".join (dataDic.values()) #e.g. 'New York' to 'New\\ York'
		else:
			dataString = "|".join (dataDic.keys())
		return (dataString)

	#-------------------------------------------------------------------
	#-- Get info of container (id, tipo)
	#-- "HLBU-208447-4 DE 40 PIES", ", "CLHU9059491 CONTENEDOR DE 40 PIES", 'INKU6519356 "40"'
	#-------------------------------------------------------------------
	def getContenedorIdTipo (text):
		try:
			reContainer = r'^(\S+).*?(\d+)\s*(?:PIES|")?'
			match       = re.search (reContainer, text)
			if match:
				id     = match.group(1).replace("-", "").replace(" ", "")
				number = match.group(2)
				return id, number
		except:
			Utils.printException ("No se pudo obtener info de contenedor en texto:", text)
		return None, None
#-------------------------------------------------------------------
# Global utility functions
#-------------------------------------------------------------------

def printx (*args, flush=True, end="\n", plain=False):
	print ("SERVER:", *args, flush=flush, end=end)


#----------------------------------------------------------
#----------------------------------------------------------
if __name__ == "__main__":
	main ()
