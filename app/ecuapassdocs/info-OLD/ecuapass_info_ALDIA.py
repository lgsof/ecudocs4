#!/usr/bin/env python3
"""
Child class for ALDIA Doc Info Classes
"""

import os, sys, re, json

from .ecuapass_info_cartaporte import CartaporteInfo
from .ecuapass_info_manifiesto import ManifiestoInfo

from .ecuapass_extractor import Extractor
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
	docFieldsPath = args [1]
	runningDir = os.getcwd ()
	CartaporteInfo = Cartaporte_ALDIA (docFieldsPath, runningDir)
	mainFields = CartaporteInfo.extractEcuapassFields ()
	Utils.saveFields (mainFields, docFieldsPath, "Results")

#----------------------------------------------------------
# Class that gets main info from Ecuapass document 
#----------------------------------------------------------
class Cartaporte_ALDIA (CartaporteInfo):
	def __init__ (self, runningDir, empresa, pais, ecudocFields=None):
		super().__init__ (runningDir, empresa, pais, ecudocFields)

	#------------------------------------------------------------------
	# No Instrucciones nor observacione
	#------------------------------------------------------------------
	def getInstruccionesObservaciones (self):
		instObs = {"instrucciones":None, "observaciones":None}
		return instObs
		
	#------------------------------------------------------------------
	#-- Return the document "pais" from docFields
	#------------------------------------------------------------------
	def getPaisDocumento (self):
		text = self.fields ["00a_Pais"]
		if "-CO-" in text:
			return "COLOMBIA"
		elif "-EC-" in text:
			return "ECUADOR"
		elif "-PE-" in text:
			return "PERU"
		else:
			print (f"+++ ERROR: Pais no identificado desde texto '{text}'")
			return None

	#------------------------------------------------------------
	# In ALDIA: Deposito in last line of field 21_Instrucciones
	#------------------------------------------------------------
	def getDepositoMercancia (self):
		try:
			text         = Utils.getValue (self.fields, "21_Instrucciones")
			lineDeposito = text.split ("\n")[-1]
			reBodega     = r':\s*(.*)'
			bodega       = Extractor.getValueRE (reBodega, lineDeposito)
			depositosDic = Extractor.getDataDic ("depositos_tulcan.txt", self.resourcesPath)
			for id, textBodega in depositosDic.items ():
				if bodega in textBodega:
					print (f"+++ Deposito '{id}' : '{textBodega}'")
					return id
			raise
		except:
			Utils.printx (f"+++ No se puedo obtener deposito desde texto '{text}'")
			return "||LOW"

	#-------------------------------------------------------------------
	# Get subject info: nombre, dir, pais, ciudad, id, idNro 
	# ALDIA format: <Nombre>\nID\n<Direccion>\n<CiudadPais>-
	#-------------------------------------------------------------------
	def getSubjectInfo (self, key):
		subject = {"nombre":"||LOW", "direccion":"||LOW", "pais": "||LOW", 
				   "ciudad":"||LOW", "tipoId":"||LOW", "numeroId": "||LOW"}
		try:
			text	   = Utils.getValue (self.fields, key)
			textLines  = text.split ("\n")

			# Case: 05_Notificado, 2 or 1 line
			if len (textLines) <= 2:
				subject = self.getSubjectInfoOneLine (subject, text)
				print (f"\n+++ Subject '{key}': '{subject}'")
				return subject

			subject ["nombre"]    = textLines [0]
			#---
			idInfo                = Extractor.getIdInfo (textLines [1])
			subject ["tipoId"]    = idInfo ["tipoId"]
			subject ["numeroId"]  = idInfo ["numeroId"]
			subject               = self.processIdTypeNum (subject)
			#---
			subject ["direccion"] = textLines [2]

			if key == "05_Notificado": # Take pais and direccion from "destinatario"
				subject ["pais"]      = self.ecudoc ["16_PaisDestinatario"]
				subject ["direccion"] = self.ecudoc ["20_DireccionDestinatario"]
			else:                      # Destinatario and Consignatario
				ciudad, pais          = Extractor.getCiudadPais (textLines [3], self.resourcesPath)
				subject ["ciudad"]    = Utils.checkLow (ciudad)
				subject ["pais"]      = Utils.checkLow (pais)
				# Add ciudad-pais to direccion
				ciudad, pais          = Extractor.getCiudadPais (textLines [3], self.resourcesPath, ECUAPASS=False)
				subject ["direccion"] = "%s. %s-%s" % (subject ["direccion"], Utils.toString (ciudad), Utils.toString (pais))

			print (f"\n+++ Subject '{key}': '{subject}'")
		except:
			Utils.printException (f"Obteniendo datos del sujeto: '{key}' en el texto: '{text}'")
		subject = Utils.checkLow (subject)
		return subject

	#-- When info is all in one line
	def getSubjectInfoOneLine (self, subject, text):
		text = text.replace ("\n","")
		text, tmpSubject = Extractor.removeSubjectId (text, subject, "05_Notificado")

		empresaTokens = ["S.A.S", "SAS", "S.A", "SA"]
		for token in empresaTokens:
			if token in text:
				index = text.index (token) + len (token)
				subject ["nombre"]    = text [:index] + "||LOW"
				subject ["direccion"] = text [index:] + "||LOW"
				subject ["pais"]    = Extractor.getPaisAndino (text) + "||LOW"
				return subject

		print (f"+++ No se pudo encontrar info subject desde texto de una linea: '{texto}'")
		return subject

#----------------------------------------------------------
# Class that gets main info from Ecuapass document 
#----------------------------------------------------------
class Manifiesto_ALDIA (ManifiestoInfo):
	def __init__(self, runningDir, empresa, pais):
		super().__init__ (runningDir, empresa, pais)

	#------------------------------------------------------------------
	#-- Return the document "pais" from docFields
	#------------------------------------------------------------------
	def getPaisDocumento (self):
		text = self.fields ["00a_Pais"]
		if "-CO-" in text:
			return "COLOMBIA"
		elif "-EC-" in text:
			return "ECUADOR"
		elif "-PE-" in text:
			return "PERU"
		else:
			print (f"+++ ERROR: Pais no identificado desde texto '{text}'")
			return None

	#------------------------------------------------------------------
	# ALDIA: Cabezote: XXXX - YYYY    Trailer: WWWW - ZZZZZ
	# Get four certificado strings. Not used for REMOLQUE in ALDIA
	#------------------------------------------------------------------
	def getCheckCertificado (self, vehicleType, key):
		# Non used in ALDIA
		if vehicleType == "REMOLQUE":
			return None

		#---------------------------------------------------
		#-- XXXX-YYYY or YYYY-XXXX In ALDIA subempresas
		def getCertificadoString (valuesList):
			if any ([x in valuesList [0] for x in ["CH", "CR"]]):
				return valuesList [0]
			elif any ([x in valuesList [1] for x in ["CH", "CR"]]):
				return valuesList [1]
			else:
				return None
		#---------------------------------------------------
		text    = self.fields [key]
		print (f"+++ textCertificado '{text}'")

		labels  = {"VEHICULO":"Cabezote", "REMOLQUE":"Trailer"}
		label   = labels [vehicleType]
		matches = re.search (rf"{label}:\s*([\w-]+)?\s*([\w-]+)?", text)
		strings = [matches.group(i) if matches and matches.group(i) else None for i in range(1, 3)]
		print (f"+++ strings '{strings}'")
		certStr = getCertificadoString (strings)

		certificado  = super().formatCertificadoString (certStr, vehicleType)
		certChecked  = self.checkCertificado (certificado, vehicleType)

		print (f"+++ Certificado '{vehicleType} : '{certChecked}'")
		return certChecked

	#----------------------------------------------------------------
	# Check if certificate string is in correct format
	#----------------------------------------------------------------
	def checkCertificado (self, certificadoString, vehicleType):
		try:
			if vehicleType == "VEHICULO":
				pattern = re.compile (r'^CH-(CO|EC)-\d{4,5}-\d{2}')
			elif vehicleType == "REMOLQUE":
				pattern = re.compile (r'^(CRU|CR)-(CO|EC)-\d{4,5}-\d{2}')

			if (certificadoString == None): 
				return "||LOW" if vehicleType == "VEHICULO" else None

			if bool (pattern.match (certificadoString)) == False:
				Utils.printx (f"Error validando certificado de <{vehicleType}> en texto: '{certificadoString}'")
				certificadoString = "||LOW"
		except:
			Utils.printException (f"Obteniendo/Verificando certificado '{certificadoString}' para '{vehicleType}'")

		return certificadoString;

	#-----------------------------------------------------------
	#-- Search for embalaje in alternate ecufield 11
	#-----------------------------------------------------------
	def getBultosInfoManifiesto (self):
		mercancia = super ().getBultosInfoManifiesto ()
		print (f"+++ mercancia parcial: '{mercancia}'")

		# Cantidad en Cantidad
		mercancia ["cantidad"] = Extractor.getNumber (self.fields ["30_Mercancia_Bultos"])
		text                   = self.fields ["31_Mercancia_Embalaje"]
		mercancia ["embalaje"] = Extractor.getTipoEmbalaje (self.fields ["31_Mercancia_Embalaje"])

		print (f"+++ Mercancia '{mercancia}'")
		return mercancia

	#-- Get marcas from cartaporte JSON file
	def getMercanciaMarcas (self, docItemKeys):
		cpiMarcas = "||LOW"
		try:
			cpiNumber      = self.fields ["28_Mercancia_Cartaporte"]
			filename       = os.path.basename (self.docFieldsPath)
			filepath       = os.path.dirname (self.docFieldsPath)

			cpiFilename    = filename.replace ("MCI", "CPI").replace (self.numero, cpiNumber)
			cpiFilepath    = os.path.join (filepath, cpiFilename)

			if os.path.exists (cpiFilepath):
				print (f"+++ Loading previous CPI document file '{cpiFilepath}'")
				cpiDocFields = json.load (open (cpiFilepath, encoding="utf-8"))
				cpiMarcas    = cpiDocFields ["11_MarcasNumeros_Bultos"]
			else:
				cpiMarcas = super ().getMercanciaMarcas (docItemKeys)
		except:
			Utils.printException ("Obteniendo marcas desde cartaporte")

		return cpiMarcas

	#-- Get Carga Tipo from docFiels 25_CargaTipo
	def getTipoCarga (self):
		cargaTipo = None
		try:
			text = self.fields ["25_Carga_Tipo"].upper ()
			print (f"+++ MANIFIESTO::getTipoCarga '{text}'")
			if  "NORMAL" in text or "SUELTA" in text:
				return "CARGA SUELTA"
			elif "GENERAL" in text:
				return "CARGA GENERAL"
			elif "CONTENERIZADA" in text:
				return "CARGA CONTENERIZADA"
			elif "GRANEL" in text:
				return "CARGA A GRANEL"
		except:
			Utils.printException ("Obteniendo Tipo de Carga")
		return cargaTipo

	#-- Get info of container (id, tipo)
#	def getContenedorIdTipo (self, text):
#		match = re.search(r'([A-Z]{4}[-\s]*\d{6,7}[-\s]*\d)?([\s]*\w+)?\s*DE\s*(\d+)\s*PIES', text)
#		match = re.search(r'([A-Z]{4}[-\s]*\d{6,7}[-\s]*\d)?([\s]*\w+)?\s*DE\s*(\d+)\s*PIES', text)
#		if match:
#			initial_string = match.group(1).replace("-", "").replace(" ", "")
#			number = match.group(3)
#			return initial_string, number
#		return None, None
#--------------------------------------------------------------------
# Call main 
#--------------------------------------------------------------------
if __name__ == '__main__':
	main ()

