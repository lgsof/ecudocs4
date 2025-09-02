
import os, json, re, datetime

from ecuapassdocs.utils.resourceloader import ResourceLoader 
from .ecuapass_data import EcuData
from .ecuapass_extractor import Extractor
from .ecuapass_utils import Utils

# Base class for all info document clases: CartaporteInfo (CPI), ManifiestoInfo (MCI), EcuDCL (DTAI)
class EcuInfo:
	def __init__ (self, docType, runningDir, empresa, pais, ecudocFields=None):
		# When called from predictions: ecudocFields, else docFieldsPath
		self.fields               = ecudocFields   # Called when predicting values
		self.docType              = docType
		self.runningDir           = runningDir
		self.empresa              = empresa
		self.pais                 = pais
		self.distrito             = None

		self.inputsParametersFile = Utils.getInputsParametersFile (docType)
		#self.empresaInfo          = EcuData.getEmpresaInfo (self.empresa)   # Overwritten per 'empresa'
		self.ecudoc               = {}                       # Ecuapass doc fields (CPI, MCI, DTI)
		self.resourcesPath        = os.path.join (runningDir, "resources", "data_ecuapass") 
#		self.numero               = self.getNumeroDocumento () # From docFields

	#------------------------------------------------------------------
	# Create Doc Info Instance for "empresa" and "docType"
	# Eg. "ecuapass_info_Cartaporte_BYZA" from "ecuapass_info_BYZA"
	# It needs to modify pyinstaller hidden modules
	#------------------------------------------------------------------
	def createDocInfoInstance (docType, empresa, pais, runningDir):
		empresaMatriz = Utils.getEmpresaMatriz (empresa)
		package       = "ecuapassdocs.info"
		module        = f"ecuapass_info_{empresaMatriz}"
		infoClass     = f"{docType.capitalize ()}_{empresaMatriz}" 
		MyClass       = ResourceLoader.load_class_from_module (package, module, infoClass)
		instance      = MyClass (runningDir, empresa, pais)  # Create an instance of the dynamically loaded class
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
		#self.pais   = Utils.getPaisFromDocNumber (self.numero)
		self.updateTipoProcedimientoFromFiels ()
		self.updateDistritoFromFields ()

	#-- Update tipo procedimiento (EXPO|INPO|TRANSITO) after knowing "Destino"
	#-- Update fecha entrega (when transito)
	def updateTipoProcedimientoFromFiels (self):
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
			distrito      = "TULCAN||LOW"
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

	#-- Return the document "pais" from docFields
	def getPaisDocumento (self):
		return self.fields ["00a_Pais"]
		#numero = self.getNumeroDocumento ()
		#pais = Utils.getPaisFromDocNumber (numero)
		#return pais

	#-- Extract numero cartaprote from doc fields
	def getNumeroCartaporte (docFields, docType):
		keys    = {"CARTAPORTE":"00_Numero", "MANIFIESTO":"28_Mercancia_Cartaporte", "DECLARACION":"15_Cartaporte"}
		text    = docFields [keys [docType]]
		text    = text.replace ("\n", "")
		numero  = Extractor.getNumeroDocumento (text)
		return numero

	#-- Extract 'fecha emision' from doc fields
	def getFechaEmision (docFields, docType, resourcesPath=None):
		fechaEmision = None
		text = None
		try:
			keys    = {"CARTAPORTE":"19_Emision", "MANIFIESTO":"40_Fecha_Emision", "DECLARACION":"23_Fecha_Emision"}
			text    = Utils.getValue (docFields, keys [docType])
			fecha   = Extractor.getDate (text, resourcesPath)
			#fecha   = fecha if fecha else datetime.datetime.today ()
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
	def getIdEmpresa (self):
		return self.empresaInfo ["id"]

	def getIdNumeroEmpresa (self):
		id = self.empresaInfo ["idNumero"]
		return id

	#-- Get full name (e.g. N.T.A Nuevo Transporte ....)
	def getNombreEmpresa (self): 
		return self.empresaInfo ["nombre"]

	#-- For NTA there are two directions: Tulcan and Huaquillas
	def getDireccionEmpresa (self):
		try:
			numero            = self.getNumeroDocumento ()
			codigoPais        = Utils.getCodigoPais (numero)
			idEmpresa         = self.getIdEmpresa ()

			if idEmpresa == "NTA" and codigoPais == "PE":
				return self.empresaInfo ["direccion02"]
			else:
				return self.empresaInfo ["direccion"]
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
			if self.pais == "COLOMBIA" and paisDestino == "PERU":
				return "TRANSITO"
			else:
				return EcuData.procedureTypes [self.pais]
				#procedimientos    = {"COLOMBIA":"IMPORTACION", "ECUADOR":"EXPORTACION", "PERU":"IMPORTACION"}
				#numero            = self.getNumeroDocumento ()
				#codigoPais        = Utils.getCodigoPais (numero)
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
			info ["pais"]   = Utils.checkLow (pais)
			info ["ciudad"] = Utils.checkLow (ciudad)

		except:
			Utils.printException ("Obteniendo informacion de 'mercancía'")

		print (f"+++ Incoterm info: '{info}'")
		return info

	#-- Get remove Inconter value (Overwritten in subclasses)
	def getRemoveIncotermPrice (self, text):
		text, number = Extractor.getRemoveNumber (text, FIRST=False)
		text         = text.replace (number, "") if number else text
		precio       = self.getEcuapassAmount (number)
		return text, precio

	#-- Get ECUAPASS value from doc field
	def getEcuapassAmountFromField (self, key):
		if key is None:
			return None

		value         = self.fields [key]
		ecuapassValue = self.getEcuapassAmount (value)
		return ecuapassValue

	#-- Get value in ECUAPASS format from value in American, Euro, or ISO formats
	def getEcuapassAmount (self, value):
		isoValue       = Utils.getISOValue (value)
		ecuapassValue  = isoValue if isoValue == value else f"{isoValue}||WARNING" 
		return ecuapassValue


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

	#----------------------------------------------------------------
	#-- Create CODEBIN fields from document fields using input parameters
	#----------------------------------------------------------------
	def getCodebinFields (self):
		try:
			inputsParams = ResourceLoader.loadJson ("docs", self.inputsParametersFile)
			codebinFields = {}
			for key in inputsParams:
				ecudocsField  = inputsParams [key]["ecudocsField"]
				codebinField  = inputsParams [key]["codebinField"]
				#print ("-- key:", key, " dfield:", ecudocsField, "cfield: ", codebinField)
				if codebinField:
					value = self.getDocumentFieldValue (ecudocsField, "CODEBIN")
					codebinFields [codebinField] = value

			return codebinFields
		except Exception as e:
			Utils.printException ("Creando campos de CODEBIN")
			return None

	#----------------------------------------------------------------
	# Create ECUAPASSDOCS fields from document fields using input parameters
	#----------------------------------------------------------------
	def getEcuapassFormFields (self):
		try:
			inputsParams = ResourceLoader.loadJson ("docs", self.inputsParametersFile)
			formFields = {}
			for key in inputsParams:
				docField   = inputsParams [key]["ecudocsField"]
				if docField == "" or "OriginalCopia" in docField:
					continue
				else:
					value = self.getDocumentFieldValue (docField)
					formFields [key] = value

			return formFields
		except Exception as e:
			Utils.printException ("Creando campos de ECUAPASSDOCS")
			return None

	#-----------------------------------------------------------
	# Get value for document field 
	#-----------------------------------------------------------
	def getDocumentFieldValue (self, docField, appName=None):
		value = None
		# For ecudocs is "CO" but for codebin is "colombia"
		if "00_Pais" in docField:
			paises     = {"CO":"CO", "EC":"EC", "PE":"PE"}
			if appName == "CODEBIN":
				paises     = {"CO":"colombia", "EC":"ecuador", "PE":"peru"}

			codigoPais = self.fields [docField]["value"]
			value      =  paises [codigoPais]

		# In PDF docs, it is a check box marker with "X"
		elif "Carga_Tipo" in docField and not "Descripcion" in docField and self.docType == "MANIFIESTO":
			fieldValue = self.fields [docField]["value"]
			value = "X" if "X" in fieldValue.upper() else ""

		else:
			value = self.fields [docField]

		return value

	#------------------------------------------------------------------
	#-- get MRN according to empresa and docField
	#------------------------------------------------------------------
	def getMRN (self):
		print (f"+++ getMRN no implementado para '{self.empresa}'")
		return "||LOW"

	#-----------------------------------------------------------
	# Get info from unidades de medida:"peso neto, volumente, otras
	#-----------------------------------------------------------
	def getTotalUnidadesInfo (self, itemKeys):
		unidades = {"pesoNeto":None, "pesoBruto": None, "volumen":None, "otraMedida":None}
		try:
			unidades ["pesoNeto"]   = self.getEcuapassAmountFromField (itemKeys ['pesoNeto'])
			unidades ["pesoBruto"]  = self.getEcuapassAmountFromField (itemKeys ['pesoBruto'])
			unidades ["volumen"]    = self.getEcuapassAmountFromField (itemKeys ['volumen'])
			unidades ["otraMedida"] = self.getEcuapassAmountFromField (itemKeys ['otraMedida'])

			print (f"\n+++ Unidades de Medida: '{unidades}'")
		except:
			Utils.printException ("Obteniendo información de 'Unidades de Medida'")
		return unidades



	def getUnidadesMedidaInfo_cartaporte (self, docItemKeys):
		unidades = {"pesoNeto":None, "pesoBruto": None, "volumen":None, "otraUnidad":None}
		try:
			unidades ["pesoNeto"]   = self.getEcuapassAmountFromField ("13a_Peso_Neto")
			unidades ["pesoBruto"]  = self.getEcuapassAmountFromField ("13b_Peso_Bruto")
			unidades ["volumen"]    = self.getEcuapassAmountFromField ("14_Volumen")
			unidades ["otraUnidad"] = self.getEcuapassAmountFromField ("15_Otras_Unidades")

			print (f"+++ Unidades de Medida: '{unidades}'")
		except:
			Utils.printException ("Obteniendo información de 'Unidades de Medida'")
		return unidades

	# Get info from unidades de medida:"peso neto, volumente, otras
	def getUnidadesMedidaInfo_Manifiesto (self):
		info = {"pesoNetoTotal":None, "pesoBrutoTotal":None, "otraUnidadTotal":None}
		try:
			info ["pesoNetoTotal"]  = Utils.checkQuantity (Extractor.getNumber (self.fields ["32a_Peso_BrutoTotal"]))
			info ["pesoBrutoTotal"]   = Utils.checkQuantity (Extractor.getNumber (self.fields ["32b_Peso_NetoTotal"]))
			info ["otraUnidadTotal"] = Utils.checkQuantity (Extractor.getNumber (self.fields ["33_Otra_MedidaTotal"]))
		except:
			Utils.printException ("'Unidades de Medida'")

		print (f"\n+++ Unidades medida '{info}'")

		return info
	#------------------------------------------------------------------
	# Get bultos info for CPI and MCI with differnte ecuapass fields
	#------------------------------------------------------------------
	def getMercanciaInfo (self, docItemKeys, analysisType="BOT"):
		mercanciaInfo = {}
		for itemKey in docItemKeys:
			value = None
			try:
				if   itemKey == "cartaporte":
					value = self.getMercanciaCartaporte (docItemKeys)
				elif itemKey == "cantidad":
					value = self.getMercanciaCantidad (docItemKeys)
				elif itemKey == "embalaje":
					value = self.getMercanciaEmbalaje (docItemKeys)
				elif itemKey == "marcas":
					value = self.getMercanciaMarcas (docItemKeys)
				elif itemKey == "pesoBruto":
					value = self.getMercanciaPesoBruto (docItemKeys)
				elif itemKey == "pesoNeto":
					value = self.getMercanciaPesoNeto (docItemKeys)
				elif itemKey == "otraMedida":
					value = self.getMercanciaOtraMedida (docItemKeys)
				elif itemKey == "descripcion":
					value = self.getMercanciaDescripcion (docItemKeys)
			except:
				Utils.printException (f"Error obteniendo item de mercancia: '{itemKey}' desde '{docItemKeys}'") 

			mercanciaInfo [itemKey] = value

		print (f"\n+++ Mercancia Info: '{mercanciaInfo}'")
		return mercanciaInfo

	def getMercanciaCartaporte (self, docItemKeys):
		if self.docType == "MANIFIESTO":
			return  Extractor.getNumeroDocumento (self.fields [docItemKeys ["cartaporte"]])
		return None
		
	def getMercanciaCantidad (self, docItemKeys):
		return Extractor.getNumber (self.fields [docItemKeys ["cantidad"]])

	def getMercanciaPesoNeto (self, docItemKeys):
		return Extractor.getNumber (self.fields [docItemKeys ["pesoNeto"]])

	def getMercanciaPesoBruto (self, docItemKeys):
		return Extractor.getNumber (self.fields [docItemKeys ["pesoBruto"]])

	def getMercanciaOtraMedida (self, docItemKeys):
		return Extractor.getNumber (self.fields [docItemKeys ["otraMedida"]])

	def getMercanciaDescripcion (self, docItemKeys):
		return self.fields [docItemKeys ["descripcion"]].strip()

	def getMercanciaEmbalaje (self, docItemKeys):
		return Extractor.getTipoEmbalaje (self.fields [docItemKeys ["embalaje"]])

	def getMercanciaMarcas (self, docItemKeys):
		marcas = self.fields [docItemKeys ["marcas"]]
		return marcas.strip() if marcas else "SIN MARCAS"

	#---------------------------------------------------------------- 
	# Return box coordinates from PDF document (CPI or MCI)
	# Coordinates file is defined in each subclass
	#---------------------------------------------------------------- 
	def getPdfCoordinates (self, pdfFilepath=None):
		coords_CPI_MCI = ResourceLoader.loadJson ("docs", self.coordinatesFile)
		coords   = coords_CPI_MCI [self.docType]
		return coords

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
					vehiculos    = {"SEMIRREMOLQUE":"SR", "TRACTOCAMION":"TC", "CAMION":"CA"}
					ecuapassFields [key] = vehiculos [ecuapassFields[key]]

				if "Moneda" in key:
					ecuapassFields [key] = "USD"

				if "Embalaje" in key: 
					embalaje = ecuapassFields [key].upper()
					ecuapassFields [key] = Extractor.getCodeEmbalaje (embalaje)

		Utils.saveFields (ecuapassFields, ecuFieldsFilepath, "UPDATE")
		return ecuapassFields

