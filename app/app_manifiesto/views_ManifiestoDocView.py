from django.urls import resolve   # To get calling URLs

# Own imports
from ecuapassdocs.utils.resourceloader import ResourceLoader 
from app_docs.views_EcuapassDocView import EcuapassDocView

#--------------------------------------------------------------------
#-- Vista para manejar las solicitudes de manifiesto
#--------------------------------------------------------------------
class ManifiestoDocView (EcuapassDocView):
	docType    = "MANIFIESTO"
	background_image = "app_docs/images/image-manifiesto-vacio-NTA-BYZA.png"
	parameters_file  = "input_parameters_manifiesto.json"

	def __init__(self, *args, **kwargs):
		super().__init__ (self.docType, self.background_image, 
		                  self.parameters_file, *args, **kwargs)

	#-- Set constant values for the BYZA company
	def initDocumentConstants (self, request):
		super ().initDocumentConstants (request)

		# Permisos values for BYZA 
		self.inputParams ["txt02"]["value"] = self.empresaInfo ["permisos"]["originario"]
		self.inputParams ["txt03"]["value"] = self.empresaInfo ["permisos"]["servicios1"]

		# Aduanas cruce/destino
		#urlName = resolve(request.path_info).url_name
		aduanaCruce,  aduanaDestino = "", ""
		#if "importacion" in urlName:
		if self.pais == "COLOMBIA":
			aduanaCruce   = "IPIALES-COLOMBIA"
			aduanaDestino = "TULCAN-ECUADOR"
		elif self.pais == "ECUADOR":
			aduanaCruce   = "TULCAN-ECUADOR"
			aduanaDestino = "IPIALES-COLOMBIA"
		else:
			print (f"Alerta: No se pudo determinar aduana cruce/destino desde país: '{self.pais}'")
		self.inputParams ["txt37"]["value"] = aduanaCruce
		self.inputParams ["txt38"]["value"] = aduanaDestino

