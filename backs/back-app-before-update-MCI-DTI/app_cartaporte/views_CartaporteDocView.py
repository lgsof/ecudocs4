import re

# Own imports
from ecuapassdocs.utils.resourceloader import ResourceLoader 
from app_docs.views_EcuapassDocView import EcuapassDocView

#--------------------------------------------------------------------
#-- Vista para manejar las solicitudes de cartaporte
#--------------------------------------------------------------------
class CartaporteDocView (EcuapassDocView):
	docType    = "CARTAPORTE"
	background_image = "app_docs/images/image-cartaporte-vacia-SILOG-BYZA.png"
	parameters_file  = "input_parameters_cartaporte.json"

	def __init__(self, *args, **kwargs):
		super().__init__ (self.docType, self.background_image, self.parameters_file, *args, **kwargs)
	
#	#----------------------------------------------------------------
#	#-- Info is embedded according to Azure format
#	#----------------------------------------------------------------
#	def getFieldValuesFromBounds (self, inputValues):
#		jsonFieldsDic = {}
#		gastosDic = {"value": {"ValorFlete":{"value":{}}, 
#		                       "Seguro":{"value":{}}, 
#							   "OtrosGastos":{"value":{}}, 
#							   "Total":{"value":{}}}}
#
#		# Load parameters from package
#		cartaporteParametersForInputs = ResourceLoader.loadJson ("docs", self.parameters_file)
#
#		for key, params in cartaporteParametersForInputs.items():
#			fieldName    = params ["ecudocsField"]
#			value        = inputValues [key]
#			if "Gastos" in fieldName:
#				res = re.findall ("\w+", fieldName)   #e.g ["ValorFlete", "MontoDestinatario"]
#				tableName, rowName, colName = res [0], res [1], res[2]
#				if value != "":
#					gastosDic ["value"][rowName]["value"][colName] = {"value": value, "content": value}
#			else:
#				jsonFieldsDic [fieldName] = {"value": value, "content": value}
#
#		jsonFieldsDic [tableName] = gastosDic
#		return jsonFieldsDic

