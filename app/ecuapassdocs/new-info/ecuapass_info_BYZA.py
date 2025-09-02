#!/usr/bin/env python3
"""
Child class for BYZA Doc Info Classes
"""

import os, sys, re

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
	fieldsJsonFile = args [1]
	runningDir = os.getcwd ()
	CartaporteInfo = CartaporteByza (fieldsJsonFile, runningDir)
	mainFields = CartaporteInfo.extractEcuapassFields ()
	Utils.saveFields (mainFields, fieldsJsonFile, "Results")

#----------------------------------------------------------
# Base class for RODFRONTE's Cartaporte and Manifiesto
#----------------------------------------------------------
class BYZA:
	#-- Remove Corebin watermark
	def getMercanciaDescripcion (self, docItemKeys):
		#------- Clean watermark in Codebin docs -------------------
		def cleanWaterMark (text):
			expression = r"(Byza)|(By\s*za\s*soluciones\s*(que\s*)*facilitan\s*tu\s*vida)"
			pattern = re.compile (expression)
			text = re.sub (pattern, '', text)
			return text.strip()
		#-----------------------------------------------------------
		docFieldKey  = docItemKeys ["descripcion"]
		descripcion  = self.fields [docFieldKey]
		descripcion  = cleanWaterMark (descripcion)

		if self.docType == "CARTAPORTE":   # Before "---" or CEC##### or "\n"
			pattern = r'((---+|CEC|\n\n).*)$'
			descripcion = re.sub (pattern, "", descripcion, flags=re.DOTALL)

		elif self.docType == "MANIFIESTO": # Before "---" or CPI: ###-###
			pattern = r'((---+|CPI:|CPIC:|\n\n).*)$'
			descripcion = re.sub (pattern, "", descripcion, flags=re.DOTALL)

		return descripcion.strip()

#----------------------------------------------------------
# Cartaporte Class that gets main info from Ecuapass document 
#----------------------------------------------------------
class Cartaporte_BYZA (BYZA, CartaporteInfo):
	def __init__ (self, empresa, pais, distrito):
		super().__init__()
		CartaporteInfo.__init__ (self, empresa, pais, distrito)
		self.daysFechaEntrega = 14

	def getMRN (self):
		return Extractor.getMRNFromText (self.fields ["12_Descripcion_Bultos"])

	#-----------------------------------------------------------
	#-- Get instrucciones y observaciones ----------------------
	#-----------------------------------------------------------
	def getInstruccionesObservaciones (self):
		instObs = {"instrucciones":None, "observaciones":None}
		return instObs

#----------------------------------------------------------
# Manifiesto Class that gets main info from Ecuapass document 
#----------------------------------------------------------
class Manifiesto_BYZA (BYZA, ManifiestoInfo):
	def __init__ (self, empresa, pais, distrito):
		super().__init__()
		ManifiestoInfo.__init__ (self, empresa, pais, distrito)

	def __str__(self):
		return f"{self.numero}"

	#-- None for BYZA 
	def getCargaDescripcion (self):
		return None

	def getMRN (self):
		return Extractor.getMRNFromText (self.fields ["29_Mercancia_Descripcion"])

	def getMercanciaEmbalaje (self, docItemKeys):
		return Extractor.getTipoEmbalaje (self.fields ['30_Mercancia_Bultos'])
#--------------------------------------------------------------------
# Call main 
#--------------------------------------------------------------------
if __name__ == '__main__':
	main ()

