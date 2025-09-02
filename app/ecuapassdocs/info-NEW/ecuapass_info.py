
import os, json, re, datetime

from ecuapassdocs.info.ecuapass_exceptions import IllegalEmpresaException

from .resourceloader import ResourceLoader 
from .ecuapass_settings import Settings
from .ecuapass_extractor import Extractor
from .ecuapass_utils import Utils

# Base class for all info document clases: CartaporteInfo (CPI), ManifiestoInfo (MCI), EcuDCL (DTAI)
class EcuInfo:
	tiposProcedimiento = {"COLOMBIA":"IMPORTACION", "ECUADOR":"EXPORTACION", "PERU":"IMPORTACION"}

	def __init__ (self, empresa, docType, pais, distrito):
		# When called from predictions: ecudocFields, else docFieldsPath
		self.empresa			  = empresa
		self.docType			  = docType
		self.pais				  = pais
		self.distrito			  = distrito
		self.fields				  = None   # Called when predicting values
		#self.fields			   = ecudocFields	# Called when predicting values

		self.inputsParametersFile = Utils.getInputsParametersFile (docType)
		self.empresaInfo		  = Settings.datos	
		self.ecudoc				  = {}						 # Ecuapass doc fields (CPI, MCI, DTI)
		runningDir				  = os.getcwd ()
		self.resourcesPath		  = os.path.join (runningDir, "resources", "data_ecuapass") 
#		self.numero				  = self.getNumeroDocumento () # From docFields
		self.numCartaportes       = 0                        # Number of doc cartaportes (MCI only)

	#------------------------------------------------------------------
	# Create Doc Info Instance for "empresa" and "docType"
	# Eg. "ecuapass_info_Cartaporte_BYZA" from "ecuapass_info_BYZA"
	# It needs to modify pyinstaller hidden modules
	#------------------------------------------------------------------
	def createDocInfoInstance (empresa, docType, pais, distrito):
		empresaMatriz = Utils.getEmpresaMatriz (empresa)
		package		  = "info"
		module		  = f"ecuapass_info_{empresaMatriz}"            # e.g. ecuapass_info_CODEBINI
		infoClass	  = f"{docType.capitalize ()}_{empresaMatriz}"  # e.g. Manifisto_CODEBINI
		infoInstance  = ResourceLoader.load_class_from_module (package, module, infoClass)
		instance	  = infoInstance (empresa, pais, distrito)	# Create an instance of the dynamically loaded class
		#instance.some_method()  # Call a method on the instance
		return instance

	#------------------------------------------------------------------
	# Set distrito from scraping class
	#------------------------------------------------------------------
	def setDistrito (self, distrito):
		self.distrito = distrito

	def getDistrito (self):
		if not self.distrito:
			self.distrito = "TULCAN" + "||LOW"
		
		return self.distrito

	#------------------------------------------------------------------
	# Update fields that depends of other fields
	#------------------------------------------------------------------
	def updateExtractedEcuapassFields (self):
		#self.numero = self.getNumeroDocumento ()
		#self.pais	 = Utils.getPaisFromDocNumber (self.numero)
		self.updateTipoProcedimientoFromFields ()
		self.updateDistritoFromFields ()

	#-- Update tipo procedimiento (EXPO|INPO|TRANSITO) after knowing "Destino"
	#-- Update fecha entrega (when transito)
	def updateTipoProcedimientoFromFields (self):
		tipoProcedimiento = self.getTipoProcedimiento ()

		procKeys = {
			"CARTAPORTE": "05_TipoProcedimiento", 
			"MANIFIESTO": "01_TipoProcedimiento", 
			"DECLARACION": "03_TipoProcedimiento"
		}
		self.ecudoc [procKeys [self.docType]] = tipoProcedimiento

	#-- Update distrito after knowing paisDestinatario
	def updateDistritoFromFields (self):
		try:
			distrito	  = "TULCAN||LOW"
			paisDestino   = self.getPaisDestinoDocumento ()

			docKeys = {
				"CARTAPORTE":  "01_Distrito",
				"MANIFIESTO":  "04_Distrito",
				"DECLARACION": "01_Distrito"
			}
			ecuapassField = docKeys [self.docType]

			# Set distrito
			if self.pais == "PERU":
				self.ecudoc [ecuapassField] = "HUAQUILLAS"
			elif self.pais == "COLOMBIA":
				self.ecudoc [ecuapassField] = "TULCAN"
			elif "PERU" in paisDestino:
				self.ecudoc [ecuapassField] = "HUAQUILLAS"
			else:
				self.ecudoc [ecuapassField] = "TULCAN"
		except Exception as ex:
			Utils.printx ("EXCEPCION actualizando distrito: '{ex}'")
	
	#-- Get doc number from docFields (azrFields)
	def getNumeroDocumento (self, docKey="00_Numero"):
		text   = self.fields [docKey]
		numero = Extractor.getNumeroDocumento (text)
		return numero

	#-- Extract numero cartaprote from doc fields
	def getNumeroCartaporte (docFields, docType):
		keys	= {"CARTAPORTE":"00_Numero", "MANIFIESTO":"28_Mercancia_Cartaporte", "DECLARACION":"15_Cartaporte"}
		text	= docFields [keys [docType]]
		text	= text.replace ("\n", "")
		numero	= Extractor.getNumeroDocumento (text)
		return numero

	#-- Extract 'fecha emision' from doc fields
	def getFechaEmision (docFields, docType, resourcesPath=None):
		fechaEmision = None
		text = None
		try:
			keys	= {"CARTAPORTE":"19_Emision", "MANIFIESTO":"40_Fecha_Emision", "DECLARACION":"23_Fecha_Emision"}
			text	= Utils.getValue (docFields, keys [docType])
			fecha	= Extractor.getDate (text, resourcesPath)
			#fecha	 = fecha if fecha else datetime.datetime.today ()
			fechaEmision = Utils.formatDateStringToPGDate (fecha)
		except:
			print (f"EXCEPCION: No se pudo extraer fecha desde texto '{text}'")
			fechaEmision = None
			#fechaEmision = datetime.today ()
		return fechaEmision

	#-- Return updated PDF document fields
	def getDocFields (self):
		return self.fields

	#-- Get id (short name: NTA, BYZA, LOGITRANS)
	def getIdNumeroEmpresa (self):
		id = self.empresaInfo ["ecuapassId"]
		return id

	#-- Get full name (e.g. N.T.A Nuevo Transporte ....)
	def getNombreEmpresa (self): 
		return self.empresaInfo ["ecuapassNombre"]

	#-- For NTA there are two directions: Tulcan and Huaquillas
	def getDireccionEmpresa (self):
		try:
			return self.empresaInfo ["ecuapassDireccion"]
		except:
			Utils.printException ("No se pudo determinar dirección empresa")
			return None

	#-----------------------------------------------------------
	#-- IMPORTACION or EXPORTACION or TRANSITO (after paisDestino)
	#-----------------------------------------------------------
	def getTipoProcedimiento (self):
		#originPais = self.getPaisOrigen ()
		print (f"+++ getTipoProcedimiento : País: '{self.pais}'")

		tipoProcedimiento = None
		paisDestino = self.getPaisDestinoDocumento ()
		try:
			if not self.pais and not self.distrito:  # Geting intial PDF info
				return None
			elif self.pais == "COLOMBIA" and paisDestino == "PERU":
				return "TRANSITO"
			else:
				return EcuInfo.tiposProcedimiento [self.pais]
				#procedimientos    = {"COLOMBIA":"IMPORTACION", "ECUADOR":"EXPORTACION", "PERU":"IMPORTACION"}
				#numero			   = self.getNumeroDocumento ()
				#codigoPais		   = Utils.getCodigoPais (numero)
				#return procedimientos [codigoPais]

		except:
			Utils.printException ("No se pudo determinar procedimiento (IMPO/EXPO/TRANSITO)")

		return "IMPORTACION||LOW"

	#-----------------------------------------------------------
	# Get info from mercancia: INCONTERM, Ciudad, Precio, Tipo Moneda
	#-----------------------------------------------------------
	def getIncotermInfo (self, docFieldsKey):
		text = self.fields [docFieldsKey]
		info = {"incoterm":None, "precio":None, "moneda":None, "pais":None, "ciudad":None}
		print (f"\n+++ Incoterm text: '{text}'")
		try:
			text = text.replace ("\n", " ")

			# Precio
			text, info ['precio'] = self.getRemoveIncotermPrice (text)

			# Incoterm
			termsString = Extractor.getDataString ("tipos_incoterm.txt", self.resourcesPath, From="keys")
			reTerms = rf"\b({termsString})\b" # RE for incoterm
			incoterm = Utils.getValueRE (reTerms, text)
			info ["incoterm"] = Utils.checkLow (incoterm)
			text = text.replace (incoterm, "") if incoterm else text

			# Moneda
			info ["moneda"] = "USD"
			text = text.replace ("USD", "")
			text = text.replace ("$", "")
			#text = text.replace ("DOLARES", "")

			# Ciudad-Pais
			ciudad, pais   = self.getCiudadPaisMultipleSources (text)
			info ["pais"]	= Utils.checkLow (pais)
			info ["ciudad"] = Utils.checkLow (ciudad)

		except:
			Utils.printException ("Obteniendo informacion de 'mercancía'")

		print (f"+++ Incoterm info: '{info}'")
		return info

	#-- Get remove Inconter value (Overwritten in subclasses)
	def getRemoveIncotermPrice (self, text):
		text, number = Extractor.getRemoveNumber (text, FIRST=False)
		text		 = text.replace (number, "") if number else text

		precio		 = self.getEcuapassNumber (number)
		return text, precio

	#-- Get ECUAPASS numerical value from doc field
	def getEcuapassValueFromField (self, key):
		ecuapassValue = self.getEcuapassNumberFromField (key)
		if not ecuapassValue:
			return None
		elif "||" in ecuapassValue and ecuapassValue.split ("||")[0]:
			ecuapassValue = ecuapassValue.split ("||")[0]
		return float (ecuapassValue)

	#-- Get ECUAPASS number with posible Warnings
	def getEcuapassNumberFromField (self, key):
		if key is None:
			return None
		text          = self.fields [key]
		value		  = Extractor.getNumber (text)
		number        = self.getEcuapassNumber (value)
		return number

	#-- Get value in ECUAPASS format from value in American, Euro, or ISO formats
	def getEcuapassNumber (self, text):
		if not text or not text.strip():
			return None

		if isinstance (text, (int, float)):
			return str (text)

		number		  = Extractor.getNumber (text)
		usValue	      = Extractor.getNumberUSFormat (number)
		Utils.log (f"getEcuapassNumber::number: {number} :: usValue: {usValue}")
		if  usValue == number or float (usValue) == 0.0: 
			return number
		elif float (usValue).is_integer() and str(int(float (usValue))) == number:
			return number
		else:
			usValue = Utils.addWarning (usValue, f"Error de formato de número.<BR>Valor original es '{text}'")
		return usValue

	def getAllEcuapassNumbers (self, text):
		allNumbers = Extractor.getNumbersAllFormats (text)
		ecuNumbers = []
		for number in allNumbers:
			ecuNumbers.append (self.getEcuapassNumber (number))
		return ecuNumbers


	#-----------------------------------------------------------
	# Get ciudad, pais either: normal search or multiple sources
	#-----------------------------------------------------------
	def getCiudadPaisMultipleSources (self, text):
		pais, ciudad = None, None
		try:
			# Default: ciudad-pais
			ciudad, pais   = Extractor.getCiudadPais (text, self.resourcesPath, ECUAPASS=True) 
			if "BOGOTA" in text:
				return "BOGOTA", "COLOMBIA"

			if ciudad and pais:
				return ciudad, pais

			# Special: Using previous boxes 
			ciudadPaisKeys = self.getCiudadPaisKeys ()
			for keys in ciudadPaisKeys:
				ciudad = Extractor.delLow (self.ecudoc [keys [0]])
				pais   = Extractor.delLow (self.ecudoc [keys [1]])
				if ciudad and pais and ciudad in text:
					return ciudad, pais
			return "",""

		except:
			Utils.printException (f"Buscando pais, ciudad con múltiples fuentes en texto: '{text}'")
		return ciudad, pais

	#------------------------------------------------------------------
	#-- get MRN searching in all doc fields
	#------------------------------------------------------------------
	def getMRN (self):
		for value in self.fields.values ():
			MRN = Extractor.getMRNFromText (value)
			if MRN:
				return MRN
		return "||LOW"

	#-----------------------------------------------------------
	# Get info from unidades de medida:"peso neto, volumente, otras
	#-----------------------------------------------------------
	def getTotalUnidadesInfo (self, docKeysItem):
		unidades = {"pesoNeto":None, "pesoBruto": None, "volumen":None, "otraMedida":None}
		try:
			unidades ["pesoNeto"]	= self.getEcuapassNumberFromField (docKeysItem ['pesoNeto'])
			unidades ["pesoBruto"]	= self.getEcuapassNumberFromField (docKeysItem ['pesoBruto'])
			volumen                 = self.getEcuapassNumberFromField (docKeysItem ['volumen'])
			unidades ["volumen"]	= Utils.addLow (volumen, "Este valor podría ir en 'Otra Unidad de Medida' en vez de Vólumen")
			unidades ["otraMedida"] = None

			print (f"\n+++ Unidades de Medida: '{unidades}'")
		except:
			Utils.printException ("Obteniendo información de 'Unidades de Medida'")
		return unidades

	#------------------------------------------------------------------
	# Get bultos info for CPI and MCI with differnte ecuapass fields
	#------------------------------------------------------------------
	def getMercanciaInfo (self, docKeysItem, analysisType="BOT"):
		mercanciaInfo = {}
		for itemKey in docKeysItem:
			value = None
			try:
				if	 itemKey == "cartaporte":
					value = self.getMercanciaCartaporte (docKeysItem)
				elif itemKey == "cantidad":
					value = self.getMercanciaCantidad (docKeysItem)
				elif itemKey == "embalaje":
					value = self.getMercanciaEmbalaje (docKeysItem)
				elif itemKey == "marcas":
					value = self.getMercanciaMarcas (docKeysItem)
				elif itemKey == "pesoBruto":
					value = self.getMercanciaPesoBruto (docKeysItem)
				elif itemKey == "pesoNeto":
					value = self.getMercanciaPesoNeto (docKeysItem)
				elif itemKey == "otraMedida":
					value = self.getMercanciaOtraMedida (docKeysItem)
				elif itemKey == "descripcion":
					value = self.getMercanciaDescripcion (docKeysItem)
			except:
				Utils.printException (f"Error obteniendo item de mercancia: '{itemKey}' desde '{docKeysItem}'") 

			mercanciaInfo [itemKey] = value

		print (f"\n+++ Mercancia Info: '{mercanciaInfo}'")
		return mercanciaInfo

	def getMercanciaCartaporte (self, docKeysItem):
		if self.docType == "MANIFIESTO":
			cartaportes         = self.getNumeroCartaporte ()
			self.numCartaportes = len (cartaportes.split ("|"))   # Some MCIs has two or more CPIs
			return cartaportes
		return None
		
	#-- Check when there are more than one value
	def getMercanciaCantidad (self, docKeysItem):
		text = self.fields [docKeysItem ["cantidad"]]
		if self.numCartaportes > 1:
			return None

		values = self.getAllEcuapassNumbers (text)
		if len (values) == 1:
			return values [0]
		elif len (values) > 1:
			#return f"{values [-1]}||WARNING:Más de un valor para cantidad"
			return Utils.addWarning (values [-1], "Más de un valor para cantidad")
		else:
			return Utils.addWarning ("", "No se encontró valor")

	#-- Search embalaje in two fields: "cantidad" and "embalaje"
	def getMercanciaEmbalaje (self, docKeysItem):
		if self.numCartaportes > 1:
			return None

		for key in ["cantidad", "embalaje"]:
			text           = self.fields [docKeysItem [key]]
			print (f"+++ getMercanciaEmbalaje text '{text}'")
			code, embalaje = Extractor.getCodeNameEmbalaje (text)
			if code and embalaje:
				return embalaje

		return "||WARNING:No se encontró valor para embalaje"


	def getMercanciaPesoNeto (self, docKeysItem):
		if self.numCartaportes > 1:    # Only valid to show for a unique value
			return None
		return self.getEcuapassNumber (self.fields [docKeysItem ["pesoNeto"]])

	def getMercanciaPesoBruto (self, docKeysItem):
		if self.numCartaportes > 1:
			return None
		return self.getEcuapassNumber (self.fields [docKeysItem ["pesoBruto"]])

	def getMercanciaOtraMedida (self, docKeysItem):
		if self.numCartaportes > 1:    # Multiple values
			return None
		return self.getEcuapassNumber (self.fields [docKeysItem ["otraMedida"]])

	def getMercanciaDescripcion (self, docKeysItem):
		if self.numCartaportes > 1:
			return None
		return self.fields [docKeysItem ["descripcion"]].strip()

#		text           = self.fields [docKeysItem ["cantidad"]]
#		code, embalaje = Extractor.getCodeNameEmbalaje (text)
#		if code and embalaje:
#			return embalaje
#		else:
#			text           = self.fields [docKeysItem ["embalaje"]]
#			code, embalaje = Extractor.getCodeNameEmbalaje (text)
#			return embalaje if code else "||LOW"

	def getMercanciaMarcas (self, docKeysItem):
		if self.numCartaportes > 1:
			return None
		marcas = self.fields [docKeysItem ["marcas"]]
		return marcas.strip() if marcas else "S/M"

	#---------------------------------------------------------------- 
	# Get last changes and prepare/Update Ecuapass doc fields 
	# with values ready to transmit
	# Change names to codes for additional presition. Remove '||LOW'
	#---------------------------------------------------------------- 
	def prepareUpdateFieldsFile (ecuFieldsFilepath):
		ecuapassFields = json.load (open (ecuFieldsFilepath, encoding="utf-8"))
		ecuapassFiels  = Utils.removeConfidenceString (ecuapassFields) # Remove cnfidence string ("||LOW")

		for key in ecuapassFields:
			if ecuapassFields [key] != None:
				if "Tipo_Vehiculo" in key:
					vehiculos	 = {"SEMIRREMOLQUE":"SR", "TRACTOCAMION":"TC", "CAMION":"CA"}
					ecuapassFields [key] = vehiculos [ecuapassFields[key]]

				if "Moneda" in key:
					ecuapassFields [key] = "USD"

				if "Embalaje" in key: 
					embalaje             = ecuapassFields [key].upper()
					code, name           = Extractor.getCodeNameEmbalaje (embalaje)
					ecuapassFields [key] = code

		Utils.saveFields (ecuapassFields, ecuFieldsFilepath, "UPDATE")
		return ecuapassFields

	#---------------------------------------------------------------- 
	#-- Set "00_XXXX" fields: docPais, docNumber, docType
	#-- Initial fields for selected PDF in GUI
	#---------------------------------------------------------------- 
	def setInitialDocFields (self):
		self.ecudoc ["00_DocEmpresa"]  = self.getNickname ()
		self.ecudoc ["00_DocType"]	   = self.docType
		self.ecudoc ["00_DocPais"]	   = self.getPaisDocumento ()   # Implemented in subclases Cartaporte y Manifiesto
		self.ecudoc ["00_DocPermiso"]  = self.getPermisoEmpresa ()
		self.ecudoc ["00_Numero"]	   = self.getNumeroDocumento ()
		self.pais    = self.getPaisDocumento ()   # Set info pais
		self.empresa = self.getNickname ()   # Set info pais

	#-- Get real empresa name
	def getNickname (self):
		return self.empresa

	def getPermisoEmpresa (self):
		try:
			permisosSettings = Settings.datos ["permiso"]
			permisosSources  = [self.fields ["00_DocPermiso"], self.fields ["01_Transportista"]]

			permisosSettingsList   = permisosSettings.split ("|")

			for permisoText in permisosSources:
				for permisoEmpresa in permisosSettingsList:
					permisoChars = Utils.removeSymbols (permisoEmpresa)
					permisoText  = Utils.removeSymbols (permisoText)

					if permisoChars and permisoChars in permisoText:
						return permisoEmpresa

			raise IllegalEmpresaException (f"SCRAPERROR::Empresa no reconocida. Problemas de permisos.")
		except Exception as ex:
			raise IllegalEmpresaException (f"SCRAPERROR::Problemas validando permisos de la empresa") from ex

