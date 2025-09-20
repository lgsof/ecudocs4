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
	

