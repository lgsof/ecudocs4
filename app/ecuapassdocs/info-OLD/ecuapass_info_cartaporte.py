#!/usr/bin/env python3

import re, os, json, sys, locale
from datetime import datetime, timedelta

from .ecuapass_info import EcuInfo
from .ecuapass_extractor import Extractor
from .ecuapass_data import EcuData
from .ecuapass_utils import Utils

#----------------------------------------------------------
USAGE = "\
Extract information from document fields analized in AZURE\n\
USAGE: ecuapass_info_cartaportes.py <Json fields document>\n"
#----------------------------------------------------------
# Main
#----------------------------------------------------------
def main ():
	args = sys.argv
	fieldsJsonFile = args [1]
	runningDir = os.getcwd ()
	mainFields = CartaporteInfo.extractEcuapassFields (fieldsJsonFile, runningDir)
	Utils.saveFields (mainFields, fieldsJsonFile, "Results")

#----------------------------------------------------------
# Class that gets main info from Ecuapass document 
#----------------------------------------------------------
class CartaporteInfo (EcuInfo):

	def __init__ (self, runningDir, empresa, pais, ecudocFields=None):
		super().__init__ ("CARTAPORTE", runningDir, empresa, pais, ecudocFields)
		self.daysFechaEntrega = 7

	#-- Get data and value from document main fields"""
	def extractEcuapassFields (self, docFieldsPath, analysisType="BOT"):
		self.fields        = json.load (open (docFieldsPath))
		self.numero        = self.getNumeroDocumento () # From docFields
		self.docFieldsPath = docFieldsPath

		#--------------------------------------------------------------
		print ("\n>>>>>> Carta de Porte Internacional por Carretera <<<")
		#--------------------------------------------------------------
		self.ecudoc ["01_Distrito"]	         = self.getDistrito ()
		self.ecudoc ["02_NumeroCPIC"]        = self.getNumeroDocumento ()
		self.ecudoc ["03_MRN"]               = self.getMRN ()
		self.ecudoc ["04_MSN"]               = self.getMSN () 
		self.ecudoc ["05_TipoProcedimiento"] = self.getTipoProcedimiento ()

		#-- Empresa
		self.ecudoc ["06_EmpresaTransporte"] = self.getNombreEmpresa ()
		self.ecudoc ["07_DepositoMercancia"] = self.getDepositoMercancia ()
		self.ecudoc ["08_DirTransportista"]	 = self.getDireccionEmpresa ()
		self.ecudoc ["09_NroIdentificacion"] = self.getIdNumeroEmpresa ()

		#--------------------------------------------------------------
		# print ("\n>>>>>> Datos Generales de la CPIC: Sujetos <<<<<<<<")
		#--------------------------------------------------------------
		#-- Remitente 
		remitente                             = Utils.checkLow (self.getSubjectInfo ("02_Remitente"))
		self.ecudoc ["10_PaisRemitente"]      = remitente ["pais"]
		self.ecudoc ["11_TipoIdRemitente"]    = remitente ["tipoId"]
		self.ecudoc ["12_NroIdRemitente"]     = remitente ["numeroId"]
		self.ecudoc ["13_NroCertSanitario"]	  = None
		self.ecudoc ["14_NombreRemitente"]    = remitente ["nombre"]
		self.ecudoc ["15_DireccionRemitente"] = remitente ["direccion"]

		#-- Destinatario 
		destinatario                             = Utils.checkLow (self.getSubjectInfo ("03_Destinatario"))
		self.ecudoc ["16_PaisDestinatario"]	     = destinatario ["pais"] 
		self.ecudoc ["17_TipoIdDestinatario"]    = destinatario ["tipoId"] 
		self.ecudoc ["18_NroIdDestinatario"]     = destinatario ["numeroId"] 
		self.ecudoc ["19_NombreDestinatario"]    = destinatario ["nombre"] 
		self.ecudoc ["20_DireccionDestinatario"] = destinatario ["direccion"] 

		#-- Consignatario 
		consignatario                             = Utils.checkLow (self.getSubjectInfo ("04_Consignatario"))
		self.ecudoc ["21_PaisConsignatario"]      = consignatario ["pais"] 
		self.ecudoc ["22_TipoIdConsignatario"]    = consignatario ["tipoId"] 
		self.ecudoc ["23_NroIdConsignatario"]     = consignatario ["numeroId"] 
		self.ecudoc ["24_NombreConsignatario"]    = consignatario ["nombre"] 
		self.ecudoc ["25_DireccionConsignatario"] = consignatario ["direccion"] 

		#-- Notificado 
		notificado                                = self.getSubjectInfo ("05_Notificado")
		self.ecudoc ["26_NombreNotificado"]	      = notificado ["nombre"] 
		self.ecudoc ["27_DireccionNotificado"]    = notificado ["direccion"] 
		self.ecudoc ["28_PaisNotificado"]         = notificado ["pais"] 

		#--------------------------------------------------------------
		# print ("\n>>>>>> Datos Generales de la CPIC: Locaciones <<<<<<<<")
		#--------------------------------------------------------------
		#-- Recepcion 
		recepcion                           = self.getLocationInfo ("06_Recepcion")
		self.ecudoc ["29_PaisRecepcion"]    = recepcion ["pais"] 
		self.ecudoc ["30_CiudadRecepcion"]  = recepcion ["ciudad"] 
		self.ecudoc ["31_FechaRecepcion"]   = recepcion ["fecha"] 

		#-- Embarque location box
		embarque                           = self.getLocationInfo ("07_Embarque")
		self.ecudoc ["32_PaisEmbarque"]    = embarque ["pais"] 
		self.ecudoc ["33_CiudadEmbarque"]  = embarque ["ciudad"] 
		self.ecudoc ["34_FechaEmbarque"]   = embarque ["fecha"] 

		#-- Entrega location box
		entrega	                          = self.getLocationInfo ("08_Entrega")
		self.ecudoc ["35_PaisEntrega"]    = entrega ["pais"] 
		self.ecudoc ["36_CiudadEntrega"]  = entrega ["ciudad"] 
		self.ecudoc ["37_FechaEntrega"]   = entrega ["fecha"] 

		#--------------------------------------------------------------
		# print ("\n>>>>>> Datos Generales de la CPIC: Condiciones <<<<<<<<")
		#--------------------------------------------------------------
		condiciones                              = Utils.checkLow (self.getCondiciones ())
		self.ecudoc ["38_CondicionesTransporte"] = condiciones ["transporte"]
		self.ecudoc ["39_CondicionesPago"]       = condiciones ["pago"]

		totalUnidades                  = self.getTotalUnidadesInfo ()
		mercanciaInfo                  = self.getMercanciaInfoCartaporte (analysisType)
		self.ecudoc ["40_PesoNeto"]	   = totalUnidades ["pesoNeto"]
		self.ecudoc ["41_PesoBruto"]   = totalUnidades ["pesoBruto"]
		self.ecudoc ["42_TotalBultos"] = mercanciaInfo ["cantidad"]
		self.ecudoc ["43_Volumen"]	   = totalUnidades ["volumen"]
		self.ecudoc ["44_OtraUnidad"]  = totalUnidades ["otraMedida"]

		# Gastos
		gastos                                     = self.getGastosInfo ()
		self.ecudoc ["50_GastosRemitente"]         = gastos ["fleteRemi"] 
		self.ecudoc ["51_MonedaRemitente"]	       = gastos ["monedaRemi"] 
		self.ecudoc ["52_GastosDestinatario"]      = gastos ["fleteDest"] 
		self.ecudoc ["53_MonedaDestinatario"]      = gastos ["monedaDest"] 
		self.ecudoc ["54_OtrosGastosRemitente"]    = gastos ["otrosRemi"] 
		self.ecudoc ["55_OtrosMonedaRemitente"]    = gastos ["otrosRemiMoneda"] 
		self.ecudoc ["56_OtrosGastosDestinatario"] = gastos ["otrosDest"] 
		self.ecudoc ["57_OtrosMonedaDestinataio"]  = gastos ["otrosDestMoneda"] 
		self.ecudoc ["58_TotalRemitente"]          = gastos ["totalRemi"] 
		self.ecudoc ["59_TotalDestinatario"]       = gastos ["totalDest"] 

		# Documentos remitente
		self.ecudoc ["60_DocsRemitente"]   = self.getDocsRemitente ()

		# Emision location box
		emision	                           = self.getLocationInfo ("19_Emision")
		self.ecudoc ["61_FechaEmision"]    = emision ["fecha"] 
		self.ecudoc ["62_PaisEmision"]     = emision ["pais"] 
		self.ecudoc ["63_CiudadEmision"]   = emision ["ciudad"] 
		
		# Incoterm
		incoterms                           = self.getIncotermInfo ("16_Incoterms")
		self.ecudoc ["45_PrecioMercancias"]	= incoterms ["precio"]
		self.ecudoc ["46_INCOTERM"]	        = incoterms ["incoterm"] 
		self.ecudoc ["47_TipoMoneda"]       = incoterms ["moneda"] 
		self.ecudoc ["48_PaisMercancia"]    = incoterms ["pais"] 
		self.ecudoc ["49_CiudadMercancia"]	= incoterms ["ciudad"] 

		# Instrucciones y Observaciones
		instObs	                           = self.getInstruccionesObservaciones ()
		self.ecudoc ["64_Instrucciones"]   = instObs ["instrucciones"]
		self.ecudoc ["65_Observaciones"]   = instObs ["observaciones"]
		#self.ecudoc ["64_Instrucciones"]   = None
		#self.ecudoc ["65_Observaciones"]   = None

		# Detalles
		self.ecudoc ["66_Secuencia"]      = "1"
		self.ecudoc ["67_TotalBultos"]    = self.ecudoc ["42_TotalBultos"]
		self.ecudoc ["68_Embalaje"]       = mercanciaInfo ["embalaje"]
		self.ecudoc ["69_Marcas"]         = mercanciaInfo ["marcas"]
		self.ecudoc ["70_PesoNeto"]	      = self.ecudoc ["40_PesoNeto"]
		self.ecudoc ["71_PesoBruto"]      = self.ecudoc ["41_PesoBruto"]
		self.ecudoc ["72_Volumen"]	      = self.ecudoc ["43_Volumen"]
		self.ecudoc ["73_OtraUnidad"]     = self.ecudoc ["44_OtraUnidad"]

		# IMOs
		self.ecudoc ["74_Subpartida"]       = None
		self.ecudoc ["75_IMO1"]             = None
		self.ecudoc ["76_IMO2"]             = None
		self.ecudoc ["77_IMO2"]             = None
		self.ecudoc ["78_NroCertSanitario"] = self.ecudoc ["13_NroCertSanitario"]
		self.ecudoc ["79_DescripcionCarga"] = mercanciaInfo ["descripcion"]

		# Update fields depending of other fields (or depending of # "empresa")
		self.updateExtractedEcuapassFields ()

		return (self.ecudoc)
	
	#------------------------------------------------------------------
	# Return ecudoc field keys containing ciudad,pais 
	#------------------------------------------------------------------
	def getCiudadPaisKeys (self):
		ciudadPaisKeys = [
				("30_CiudadRecepcion", "29_PaisRecepcion"),
				("33_CiudadEmbarque", "32_PaisEmbarque"),
				("36_CiudadEntrega", "35_PaisEntrega"),
				("63_CiudadEmision", "62_PaisEmision")]
		return ciudadPaisKeys
			
	#------------------------------------------------------------------
	#-- First level functions for each Ecuapass field
	#------------------------------------------------------------------
	def getMSN (self):
		return "0001||LOW"

	#-- Get MRN from multiple fields
	def getMRN (self):
		MRN = Extractor.getMRNFromText (self.fields ["12_Descripcion_Bultos"])
		if not MRN:
			MRN = Extractor.getMRNFromText (self.fields ["21_Instrucciones"])
			if not MRN:
				MRN = Extractor.getMRNFromText (self.fields ["22_Observaciones"])
		return MRN if MRN else "||LOW" 
	#------------------------------------------------------------
	# Return the code number from the text matching a "deposito"
	#-- BOTERO-SOTO en casilla 21 o 22, NTA en la 22 ------------
	#------------------------------------------------------------
	def getDepositoMercancia (self):
		for casilla in ["21_Instrucciones", "22_Observaciones"]:
			text = ""
			try:
				text        = self.fields [casilla]
				reWordSep  = r'\s+(?:EL\s+)?'
				#reBodega    = rf'BODEGA[S]?\s+\b(\w*)\b'
				reBodega    = rf'BODEGA[S]?{reWordSep}\b(\w*)\b'
				bodegaText  = Extractor.getValueRE (reBodega, text)
				if bodegaText != None:
					Utils.printx (f"Extrayendo código para el deposito '{bodegaText}'")
					depositosDic = Extractor.getDataDic ("depositos_tulcan.txt", self.resourcesPath)
					
					for id in depositosDic:
						if bodegaText in depositosDic [id]:
							return id
			except:
				Utils.printException (f"Obteniendo bodega desde texto '{text}'")
		return "||LOW"

	#-------------------------------------------------------------------
	#-- Get location info: ciudad, pais, fecha -------------------------
	#-- Boxes: Recepcion, Embarque, Entrega ----------------------------
	#-------------------------------------------------------------------
	def getLocationInfo (self, key):
		text     = self.fields [key]
		location = Extractor.extractLocationDate (text, self.resourcesPath, key)
		print (f"+++ Location/Date text for '{key}': '{location}'")
		if key == "08_Entrega" and location ["fecha"] == "||LOW":
			location ["fecha"] = self.getFechaEntrega (location["fecha"])

		print (f"+++ Location/Date info for '{key}': '{location}'")
		return (location)

	#-- Called when update extracted fields
	#-- Add one or tww weeks to 'entrega' from 'embarque' date
	def getFechaEntrega (self, fechaEntrega=None):
		fechaEmbarque = None
		try:
			if fechaEntrega == "||LOW" or fechaEntrega is None:
				fechaEmbarque = self.ecudoc ["34_FechaEmbarque"]
				fechaEmbarque = datetime.strptime (fechaEmbarque, "%d-%m-%Y") # Fecha igual a la de Embarque
				fechaEntrega  = fechaEmbarque + timedelta (days=self.daysFechaEntrega)

				if self.getTipoProcedimiento () == "TRANSITO":
					fechaEntrega = fechaEmbarque + timedelta (days=2*self.daysFechaEntrega)

				fechaEntrega = fechaEntrega.strftime ("%d-%m-%Y") + "||LOW"
				return fechaEntrega
		except:
			Utils.printException ("ERROR: Calculando fecha entrega desde fecha embarque:", fechaEmbarque)

		return fechaEntrega

	#-----------------------------------------------------------
	# Get "transporte" and "pago" conditions
	#-----------------------------------------------------------
	def getCondiciones (self):
		conditions = {'pago':None, 'transporte':None}
		# Condiciones transporte
		text = self.fields ["09_Condiciones"].upper ()
		try:
			if "SIN CAMBIO" in text or "SIN TRASBORDO" in text:
				conditions ["transporte"] = "DIRECTO, SIN CAMBIO DEL CAMION"
			elif "CON CAMBIO" in text or "CON TRASBORDO" in text:
				conditions ["transporte"] = "DIRECTO, CON CAMBIO DEL TRACTO-CAMION"
			elif "TRANSBORDO" in text or "TRASBORDO" in text: 
				conditions ["transporte"] = "TRANSBORDO"
		except:
			Utils.printException ("Extrayendo condiciones de transporte en texto", text)

		# Condiciones pago
		try:
			if "CREDITO" in text:
				conditions ["pago"] = "POR COBRAR||LOW"
			elif "ANTICIPADO" in text:
				conditions ["pago"] = "PAGO ANTICIPADO||LOW"
			elif "CONTADO" in text:
				conditions ["pago"] = "PAGO ANTICIPADO||LOW"
			else:
				pagoString = Extractor.getDataString ("condiciones_pago.txt", self.resourcesPath)
				rePagos    = rf"\b({pagoString})\b" # RE to find a match string
				pago       = Extractor.getValueRE (rePagos, text)
				conditions ["pago"] = pago if pago else "POR COBRAR||LOW"
		except:
			Utils.printException ("Extrayendo condiciones de pago en texto:", text)

		print (f"+++ Condiciones Pago/Transporte '{conditions}'")
		return (conditions)

	#-----------------------------------------------------------
	# Get info from unidades de medida:"peso neto, volumente, otras
	#-----------------------------------------------------------
	def getTotalUnidadesInfo (self):
		docItemKeys = {'pesoBruto':'13b_Peso_Bruto', 'pesoNeto':'13a_Peso_Neto', 
		               'volumen':'14_Volumen', 'otraMedida':'15_Otras_Unidades'}
		return super ().getTotalUnidadesInfo (docItemKeys)

#	def getUnidadesMedidaInfo (self):
#		unidades = {"pesoNeto":None, "pesoBruto": None, "volumen":None, "otraUnidad":None}
#		try:
#			unidades ["pesoNeto"]   = self.getEcuapassAmountFromField ("13a_Peso_Neto")
#			unidades ["pesoBruto"]  = self.getEcuapassAmountFromField ("13b_Peso_Bruto")
#			unidades ["volumen"]    = self.getEcuapassAmountFromField ("14_Volumen")
#			unidades ["otraUnidad"] = self.getEcuapassAmountFromField ("15_Otras_Unidades")
#
#			print (f"+++ Unidades de Medida: '{unidades}'")
#		except:
#			Utils.printException ("Obteniendo información de 'Unidades de Medida'")
#		return unidades

	#-----------------------------------------------------------
	# Get 'total bultos' and 'tipo embalaje' 
	# Uses base function "getMercanciaInfo" with cartaporte fields
	#-----------------------------------------------------------
	def getMercanciaInfoCartaporte (self, analysisType="BOT"):
		ecuapassFields = {"cantidad":"10_CantidadClase_Bultos", "marcas":"11_MarcasNumeros_Bultos", 
					"descripcion":"12_Descripcion_Bultos", 'pesoNeto':'13a_Peso_Neto', 'embalaje':'10_CantidadClase_Bultos',
					'pesoBruto':'13b_Peso_Bruto', 'volumen':'14_Volumen', 'otraMedida':'15_Otras_Unidades'}       

		mercanciaInfo = super().getMercanciaInfo (ecuapassFields, analysisType)
		return mercanciaInfo

	#--------------------------------------------------------------------
	#-- Search "pais" for "ciudad" in previous document boxes
	#--------------------------------------------------------------------
	def searchPaisPreviousBoxes (self, ciudad, pais):
		try:
			# Search 'pais' in previos boxes
			if (ciudad != None and pais == None):
				if self.ecudoc ["30_CiudadRecepcion"] and ciudad in self.ecudoc ["30_CiudadRecepcion"]:
					pais = self.ecudoc ["29_PaisRecepcion"]
				elif self.ecudoc ["33_CiudadEmbarque"] and ciudad in self.ecudoc ["33_CiudadEmbarque"]:
					pais = self.ecudoc ["32_PaisEmbarque"]
				elif self.ecudoc ["36_CiudadEntrega"] and ciudad in self.ecudoc ["36_CiudadEntrega"]:
					pais = self.ecudoc ["35_PaisEntrega"]

		except:
			Utils.printException ("Obteniendo informacion de 'mercancía'")
		return ciudad, pais

	#-----------------------------------------------------------
	# Get info from 'documentos recibidos remitente'
	#-----------------------------------------------------------
	def getDocsRemitente (self):
		docs = None
		try:
			docs = self.fields ["18_Documentos"]
			print (f"+++ Documentos info: '{docs}'")
		except:
			Utils.printException("Obteniendo valores 'DocsRemitente'")
		return docs

	#-----------------------------------------------------------
	#-- Get instrucciones y observaciones ----------------------
	#-----------------------------------------------------------
	def getInstruccionesObservaciones (self):
		instObs = {"instrucciones":None, "observaciones":None}
		try:
			instObs ["instrucciones"] = self.fields ["21_Instrucciones"]
			instObs ["observaciones"] = self.fields ["22_Observaciones"]
			print (f"+++ 21: Instrucciones info: {instObs['instrucciones']}")
			print (f"+++ 22: Observaciones info: {instObs['observaciones']}")
		except:
			Utils.printException ("Obteniendo informacion de 'Instrucciones y Observaciones'")
		return instObs

	#-----------------------------------------------------------
	# Get 'gastos' info: monto, moneda, otros gastos
	#-----------------------------------------------------------
	def getGastosInfo (self):
		gastos = {"fleteRemi":None, "monedaRemi":None,       "fleteDest":None,       "monedaDest":None,
			"otrosRemi":None, "otrosRemiMoneda":None, "otrosDest":None, "otrosDestMoneda": None,
			"totalRemi":None, "totalRemiMoneda": None, "totalDest":None, "totalDestMoneda":None}
		try:
			# DESTINATARIO:
			gastos ["fleteDest"]	   = self.getEcuapassAmountFromField ("17_Gastos:ValorFlete,MontoDestinatario")
			gastos ["seguroDest"]      = self.getEcuapassAmountFromField ("17_Gastos:Seguro,MontoDestinatario")
			gastos ["otrosDest"]       = self.getEcuapassAmountFromField ("17_Gastos:OtrosGastos,MontoDestinatario")
			gastos ["totalDest"]       = self.getEcuapassAmountFromField ("17_Gastos:Total,MontoDestinatario")

			# REMITENTE: 
			gastos ["fleteRemi"]       = self.getEcuapassAmountFromField ("17_Gastos:ValorFlete,MontoRemitente")
			gastos ["seguroRemi"]      = self.getEcuapassAmountFromField ("17_Gastos:Seguro,MontoRemitente")
			gastos ["otrosRemi"]       = self.getEcuapassAmountFromField ("17_Gastos:OtrosGastos,MontoRemitente")
			gastos ["totalRemi"]       = self.getEcuapassAmountFromField ("17_Gastos:Total,MontoRemitente")

			gastos ["monedaDest"]      = "USD" if str (gastos ["fleteDest"]) else None
			gastos ["otrosDestMoneda"] = "USD" if str (gastos ["otrosDest"]) else None
			gastos ["totalDestMoneda"] = "USD" if str (gastos ["totalDest"]) else None
			gastos ["monedaRemi"]      = "USD" if str (gastos ["fleteRemi"]) else None
			gastos ["otrosRemiMoneda"] = "USD" if str (gastos ["otrosRemi"]) else None
			gastos ["totalRemiMoneda"] = "USD" if str (gastos ["totalRemi"]) else None

			print (f"\n+++ Gastos Info: '{gastos}'")
			gastos = self.totalizeCheckGastos (gastos)

		except:
			Utils.printException ("Obteniendo valores de 'gastos'")

		print (f"\n+++ Gastos info totals: '{gastos}'")
		return gastos

	#-------------------------------------------------------------------
	# Totalize  "OtroGastos" by summing "Otros" and "Seguro"
	# Check Totals if are the sum of single items
	#-------------------------------------------------------------------
	def totalizeCheckGastos (self, gastos):
		#---------------------------------------------------------------
		def FLOAT (value):
			return float (Utils.getISOValue (value)) if value else 0.0
		#---------------------------------------------------------------
		def totalizeOtros (keys):
			monedaKey, totalKey, valuesKeys = keys [0], keys [1], keys [1:]
			try:
				if gastos [keys [1]] or gastos [keys [2]]:
					gastos [totalKey]  = sum ([FLOAT (gastos [k]) for k in valuesKeys])
					gastos [monedaKey] = 'USD'
			except:
				Utils.printException (f'ERROR: calculando totales')
				handleException (totalKey, valuesKeys)
		#---------------------------------------------------------------
		def checkTotals (keys):
			totalKey = keys [0]
			try:
				valuesKeys = keys [1:]
				total = sum ([FLOAT (gastos [k]) for k in valuesKeys])
				if total != FLOAT (gastos [totalKey]):
					raise ValueError
			except:
				Utils.printException (f'ERROR: comparando totales: calculado vs. documento')
				handleException (totalKey, keys)
		#---------------------------------------------------------------
		def handleException (totalKey, valuesKeys):
			for k in valuesKeys.extend ([totalKey]):
				if 'ERROR' not in str (gastos [k]):
					gastos [k] = (str(gastos [k]) or '') + '||ERROR' 
		#---------------------------------------------------------------

		locale.setlocale(locale.LC_NUMERIC, 'en_US.UTF-8')
		# Totalize 'otrosXXX'
		totalizeOtros (['otrosRemiMoneda', 'otrosRemi', 'seguroRemi'])
		totalizeOtros (['otrosDestMoneda', 'otrosDest', 'seguroDest'])
		
		# Check Totals if correspond to the sum of the values
		checkTotals (['totalRemi', 'fleteRemi', 'otrosRemi'])
		checkTotals (['totalDest', 'fleteDest', 'otrosDest'])

		return gastos

	#-------------------------------------------------------------------
	#-- Get subject info: nombre, dir, pais, ciudad, id, idNro ---------
	#-- NTA format: <Nombre> <Direccion> <ID> <PaisCiudad> -----
	#-------------------------------------------------------------------
	#-- Get subject info: nombre, dir, pais, ciudad, id, idNro
	def getSubjectInfo (self, key):
		
		subject = Utils.createEmptyDic (["nombre","direccion","pais","ciudad","tipoId","numeroId"])
		text	= self.fields [key]
		print (f"\n\n+++ SubjectInfo for '{key}' in text:\n{text}")
		try:
			text, subject = Extractor.removeSubjectId (text, subject, key)
			subject       = self.processIdTypeNum (subject)
			print (f"+++ Subject Info: Removed Id '{subject}'\n'{text}'")
			text, subject = Extractor.removeSubjectCiudadPais (text, subject, self.resourcesPath, key)
			print (f"+++ Subject Info: Removed Ciudad-Pais '{subject}'\n'{text}'")
			text, subject = Extractor.removeSubjectNombreDireccion (text, subject, key)
			print (f"+++ Subject Info: Removed NombreDireccion '{subject}'\n'{text}'")
		except:
			Utils.printException (f"Obteniendo datos del sujeto: '{key}' en el texto:\n'{text}'")

		print (f"+++ Subject info: '{subject}'")
		return (subject)

	#-------------------------------------------------------------------
	def processIdTypeNum (self, subject):
		tipoId, numeroId = subject ['tipoId'], subject ['numeroId']
		try:
			if tipoId == "NIT":
				subject ['tipoId']   = "OTROS||WARNING"
				subject ['numeroId'] = numeroId.split ("-")[0] + '||WARNING'
		except:
			Utils.printException ('Error: No se pudo procesar cliente tipo id o número:', tipoId, numeroId) 
		return subject
	#-------------------------------------------------------------------
	
	#-------------------------------------------------------------------
	# Origin pais determines the procedure type: IMPORTACION or EXPORTACION
	#-------------------------------------------------------------------
	def getPaisOrigen (self):
		p1 = Utils.toString (Extractor.delLow (self.ecudoc ["10_PaisRemitente"]))
		p2 = Utils.toString (EExtractor.delLow (self.ecudoc ["29_PaisRecepcion"]))
		p3 = Utils.toString (EExtractor.delLow (self.ecudoc ["62_PaisEmision"]))

		if p1 == p2 or p1 == p3:
			return p1
		elif p2 == p1 or p2 == p3:
			return p2
		elif p3 == p1 or p3 == p2:
			return p3
		else: 
			return None

	#-------------------------------------------------------------------
	#-- Get pais destinatario
	#-------------------------------------------------------------------
	def getPaisDestinatario (self):
		return self.ecudoc ["16_PaisDestinatario"]

	#-----------------------------------------------------------
	#-----------------------------------------------------------
	# Basic functions
	#-----------------------------------------------------------
	#-----------------------------------------------------------
	def getPaisDestinoDocumento (self):
		try:
			paisDestino = self.getPaisDestinatario ()
			if not paisDestino:
				paisDestino = self.ecudoc ["35_PaisEntrega"] 
			return paisDestino
		except:
			return None

#--------------------------------------------------------------------
# Call main 
#--------------------------------------------------------------------
if __name__ == '__main__':
	main ()

