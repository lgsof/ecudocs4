import os, tempfile, json

from django.db import models
from django.urls import reverse  # To generate URLS by reversing URL patterns

from ecuapassdocs.info.ecuapass_utils import Utils

from app_docs.models_docbase import DocBaseModel
from app_cartaporte.models_doccpi import Cartaporte
from ecuapassdocs.utils.models_scripts import Scripts
from app_entidades.models_Entidades import Vehiculo, Conductor

#--------------------------------------------------------------------
# Model ManifiestoForm
#--------------------------------------------------------------------
class ManifiestoForm (models.Model):
	class Meta:
		db_table = "manifiestoform"

	numero = models.CharField (max_length=20)

	txt0a = models.CharField (max_length=20, null=True)
	txt01 = models.CharField (max_length=20, null=True)
	txt00 = models.CharField (max_length=20, null=True)
	txt01 = models.CharField (max_length=200, null=True)
	txt02 = models.CharField (max_length=200, null=True)
	txt03 = models.CharField (max_length=200, null=True)
	txt04 = models.CharField (max_length=200, null=True)
	txt05 = models.CharField (max_length=200, null=True)
	txt06 = models.CharField (max_length=200, null=True)
	txt07 = models.CharField (max_length=200, null=True)
	txt08 = models.CharField (max_length=200, null=True)
	txt09 = models.CharField (max_length=200, null=True)
	txt10 = models.CharField (max_length=200, null=True)
	txt11 = models.CharField (max_length=200, null=True)
	txt12 = models.CharField (max_length=200, null=True)
	txt13 = models.CharField (max_length=200, null=True)
	txt14 = models.CharField (max_length=200, null=True)
	txt15 = models.CharField (max_length=200, null=True)
	txt16 = models.CharField (max_length=200, null=True)
	txt17 = models.CharField (max_length=200, null=True)
	txt18 = models.CharField (max_length=200, null=True)
	txt19 = models.CharField (max_length=200, null=True)
	txt20 = models.CharField (max_length=200, null=True)
	txt21 = models.CharField (max_length=200, null=True)
	txt22 = models.CharField (max_length=200, null=True)
	txt23 = models.CharField (max_length=200, null=True)
	txt24 = models.CharField (max_length=200, null=True)
	txt25_1 = models.CharField (max_length=200, null=True)
	txt25_2 = models.CharField (max_length=200, null=True)
	txt25_3 = models.CharField (max_length=200, null=True)
	txt25_4 = models.CharField (max_length=200, null=True)
	txt25_5 = models.CharField (max_length=200, null=True)
	txt26 = models.CharField (max_length=200, null=True)
	txt27 = models.CharField (max_length=200, null=True)
	#-- Info mercancia (cartaporte, descripcion, ...totales ----
	txt28 = models.CharField (max_length=200, null=True)    # Cartaporte
	txt29 = models.TextField (null=True, blank=True)        # Descripcion
	txt30 = models.CharField (max_length=200, null=True)    # Cantidad
	txt31 = models.CharField (max_length=200, null=True)    # Marca
	txt32_1 = models.CharField (max_length=200, null=True)  # Peso bruto
	txt32_2 = models.CharField (max_length=200, null=True)  # Peso bruto total
	txt32_3 = models.CharField (max_length=200, null=True)  # Peso neto
	txt32_4 = models.CharField (max_length=200, null=True)  # Peso neto total
	txt33_1 = models.CharField (max_length=200, null=True)  # Otra medida
	txt33_2 = models.CharField (max_length=200, null=True)  # Otra medida total
	txt34 = models.CharField (max_length=200, null=True)    # INCOTERMS
	#------------------------------------------------------------
	txt35 = models.CharField (max_length=200, null=True)
	txt37 = models.CharField (max_length=200, null=True)    # Aduana cruce
	txt38 = models.CharField (max_length=200, null=True)    # Aduana destino
	txt40 = models.CharField (max_length=200, null=True)

	def getConductor (self):
		return self.txt13

	def __str__ (self):
		return f"{self.numero}, {self.txt03}"
	
	def setMercanciaInfo (self, mercanciaInfo):
		self.txt20 = mercanciaInfo ["cartaporte"]
		self.txt29 = mercanciaInfo ["descripcion"]
		self.txt30 = mercanciaInfo ["cantidad"]
		self.txt31 = mercanciaInfo ["marcas"]

	def getInputValuesFromInfo (infoFromCPI):
		print (f"+++ infoFromCPI '{infoFromCPI}'")
		inputValues = {}
		inputValues ["txt0a"]	= infoFromCPI ["pais"]
		inputValues ["txt02"]	= infoFromCPI ["permisoOriginario"]
		inputValues ["txt03"]	= infoFromCPI ["permisoServicios"]
		inputValues ["txt28"]	= infoFromCPI ["cartaporte"]
		inputValues ["txt29"]	= infoFromCPI ["descripcion"]
		inputValues ["txt30"]	= infoFromCPI ["cantidad"]
		inputValues ["txt31"]	= infoFromCPI ["marcas"]
		inputValues ["txt32_1"] = infoFromCPI ["pesoBruto"]
		inputValues ["txt32_3"] = infoFromCPI ["pesoNeto"]
		inputValues ["txt33_1"]	= infoFromCPI ["otrasUnd"]
		inputValues ["txt34"]	= infoFromCPI ["incoterms"]
		inputValues ["txt37"]	= infoFromCPI ["aduanaCruce"]
		inputValues ["txt38"]	= infoFromCPI ["aduanaDestino"]
		inputValues ["txt40"]	= infoFromCPI ["fechaEmision"]

		# Predicted info for "Vehiculo"
		inputValues ["txt04"]	= infoFromCPI ["marcaVehiculo"] 
		inputValues ["txt05"]	= infoFromCPI ["anhoVehiculo"]
		inputValues ["txt06"]	= infoFromCPI ["placaPaisVehiculo"]
		inputValues ["txt07"]	= infoFromCPI ["chasisVehiculo"]
		# Predicted info for "Remolque"
		inputValues ["txt09"]	= infoFromCPI ["marcaRemolque"]
		inputValues ["txt10"]	= infoFromCPI ["anhoRemolque"]
		inputValues ["txt11"]	= infoFromCPI ["placaPaisRemolque"]
		inputValues ["txt12"]	= infoFromCPI ["chasisRemolque"]
		# Predicted info for "Conductor"
		inputValues ["txt13"]	= infoFromCPI ["nombreConductor"]
		inputValues ["txt14"]	= infoFromCPI ["documentoConductor"]
		inputValues ["txt15"]	= infoFromCPI ["paisConductor"]
		inputValues ["txt16"]	= infoFromCPI ["licenciaConductor"]
		# Predicted info for "Auxiliar"
		inputValues ["txt18"]	= infoFromCPI ["nombreAuxiliar"]
		inputValues ["txt19"]	= infoFromCPI ["documentoAuxiliar"]
		inputValues ["txt20"]	= infoFromCPI ["paisAuxiliar"]
		inputValues ["txt21"]	= infoFromCPI ["licenciaAuxiliar"]

		# Datos sobre la carga
		inputValues ["txt23"]	= infoFromCPI ["ciudadPaisCarga"]
		inputValues ["txt24"]	= infoFromCPI ["ciudadPaisDescarga"]
		inputValues ["txt25_4"]	= infoFromCPI ["otroTipoCarga"]
		inputValues ["txt25_5"]	= infoFromCPI ["descripcionCarga"]

		# Aduanas info
		inputValues ["txt37"]	= infoFromCPI ["aduanaCruce"]
		inputValues ["txt38"]	= infoFromCPI ["aduanaDestino"]

		return inputValues





#--------------------------------------------------------------------
# Model Manifiesto
#--------------------------------------------------------------------
class Manifiesto (DocBaseModel):
	class Meta:
		db_table = "manifiesto"

	documento     = models.OneToOneField (ManifiestoForm, on_delete=models.CASCADE, null=True)
	vehiculo      = models.ForeignKey (Vehiculo, on_delete=models.SET_NULL, related_name='manifiestos', null=True)
	conductor     = models.ForeignKey (Conductor, on_delete=models.SET_NULL, related_name='manifiestos', null=True)
	cartaporte    = models.ForeignKey (Cartaporte, on_delete=models.SET_NULL, related_name="manifiestos", null=True)

	#-- Get str for printing
	def __str__ (self):
		return f"{self.numero}, {self.conductor}"

	def setValues (self, manifiestoForm, docFields, pais, username):
		# Base values
		super().setValues (manifiestoForm, docFields, pais, username)

		# Document values
#		placaPais        = manifiestoInfo.getPlacaPais ()
#		conductor        = manifiestoInfo.getConductor ()
#		cartaporteNumber = manifiestoInfo.getNumeroCartaporte ()
#		descripcion      = manifiestoInfo.getDescripcion ()
#		referencia       = manifiestoInfo.getReferencia ()
#
#		self.cartaporte  = Scripts.getCartaporteInstanceByNumero (cartaporteNumber)
#		print (f"\t+++ cartaporte instance:'{self.cartaporte}'")
#
#		self.getSaveVehiculoConductorInstance (manifiestoInfo)
#		self.fecha_emision = EcuInfo.getFechaEmision (docFields, "MANIFIESTO")

		#self.updateFieldRelations ()

		def getDocPlacaPais (self, docFields):
			placaPais = Extractor.getPlacaPais (docFields ["06_Camion_PlacaPais"], self.resourcesPath) 
            

	#-- Get and save info vehiculo/remolque/conductor/auxiliar
	def getSaveVehiculoConductorInstance (self, manifiestoInfo):
		# Vehiculo
		veinfo = manifiestoInfo.extractVehiculoInfo (type="VEHICULO")
		vehiculo, changeFlag = self.getSaveUpdateInstance ("vehiculo", veinfo)

		# Remolque
		reinfo = manifiestoInfo.extractVehiculoInfo (type="REMOLQUE")
		remolque, changeFlag = self.getSaveUpdateInstance ("vehiculo", reinfo)

		# Conductor
		coinfo = manifiestoInfo.extractConductorInfo ()
		conductor, changeFlag = self.getSaveUpdateInstance ("conductor", coinfo)

		if vehiculo:
			self.updateInstanceFromVehiculo (conductor, vehiculo)
			self.updateInstanceFromVehiculo (remolque, vehiculo)

		self.vehiculo = vehiculo
		self.save ()

	#-- Update/set Remolque, Conductor to Vehiculo
	def updateInstanceFromVehiculo (self, instance, vehiculo):
		if not instance or not vehiculo: 
			return
		# Instance is in another Vehiculo	
		if instance.__class__ == Vehiculo:      # Remolque
			vehiculo.remolque = instance
		elif instance.__class__ == Conductor:   # Conductor
			vehiculo.conductor = instance

		vehiculo.save ()

	#-- Get or create, and save instance and flags if it was created or it has changed
	def getSaveUpdateInstance (self, instanceName, info):
		instance, changeFlag = None, False
		try:
			if instanceName == "vehiculo":
				if info ['placa']:
					instance, createFlag = Vehiculo.objects.get_or_create (placa=info ['placa'])
			elif instanceName == "conductor":
				if info ['documento']:
					instance, createFlag = Conductor.objects.get_or_create (documento=info ['documento'])
			else:
				raise Exception (f"Tipo entidad '{instanceName}' no existe")

			if instance:
				for key in info.keys ():
					if getattr (instance, key) != info [key]:
						setattr (instance, key, info [key])
						changeFlag = True

				if createFlag or changeFlag:
					instance.save ()
		except:
			Utils.printException (f"Error con nombre de instancia '{instanceName}'")
		return instance, changeFlag


	#-- Get cartaporte from manifiesto info
	def getCartaporteInstance (self, manifiestoInfo):
		cartaporteNumber = None
		try:
			cartaporteNumber = manifiestoInfo.getNumeroCartaporte ()
			instance = Cartaporte.objects.get (numero=cartaporteNumber)
			return instance
		except: 
			Utils.printx (f"ALERTA: Cartaporte número '{cartaporteNumber}' no encontrado.")
			#Utils.printException ()
		return None

	#-- Get a 'conductor' instance from extracted info
	def getSaveConductorInstance (self, manifiestoInfo, vehicleType):
		try:
			info = manifiestoInfo.extractConductorInfo ()
			print (f"+++ DEBUG: info conductor '{info}'")
			if any (Utils.isEmptyFormField (text) for text in info.values()):
				return None
			else:
				conductor, created  = Conductor.objects.get_or_create (documento=info['id'])
				conductor.pais            = info ["pais"]
				conductor.tipoId          = info ["tipoId"]
				conductor.id              = info ["id"]
				conductor.sexo            = info ["sexo"]
				conductor.fecha_nacimiento = info ["fecha_nacimiento"]
				conductor.licencia        = info ["licencia"]
				conductor.save ()
				return conductor
		except:
			Utils.printException (f"Obteniedo información del vehiculo.")
			return None

	#-- Get a 'vehiculo' instance from extracted info
	def getSaveVehiculoInstance (self, manifiestoInfo, vehicleType):
		print ("+++ Tipo vehiculo:", vehicleType)
		try:
			info = manifiestoInfo.extractVehiculoInfo (vehicleType)
			if any (value is None for value in info.values()):
				return None
			else:
				vehiculo, createdFlag = Vehiculo.objects.get_or_create (placa=info['placa'])
				vehiculo.marca        = info ["marca"]
				vehiculo.placa        = info ["placa"]
				vehiculo.pais         = info ["pais"]
				vehiculo.chasis       = info ["chasis"]
				vehiculo.anho         = info ["anho"]
				vehiculo.certificado  = info ["certificado"]
				vehiculo.save ()
				return vehiculo
		except:
			Utils.printException (f"Obteniedo información del vehiculo.")
			return None

	def createTemporalJson (self, docFields):
		tmpPath        = tempfile.gettempdir ()
		jsonFieldsPath = os.path.join (tmpPath, f"MANIFIESTO-{self.numero}.json")
		json.dump (docFields, open (jsonFieldsPath, "w"))
		return (jsonFieldsPath, tmpPath)


    #------------------------------------------------------
    # Get initial values from cartaporte
    #------------------------------------------------------
    #def getInitialValuesFromCartaporte (cartaporteNumber):
    #def getInitialValuesFromEmpresa (empresaName):

