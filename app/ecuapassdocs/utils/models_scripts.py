"""
Scripts for read/write models into DB
"""
import os
from datetime import timedelta

from django.utils import timezone # For getting recent cartaportes
from django.conf import settings         # BASE_DIR

# For advance DB search on texts
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import F

from ecuapassdocs.info.ecuapass_utils import Utils
from ecuapassdocs.utils.docutils import DocUtils
from ecuapassdocs.info.ecuapass_extractor import Extractor

# For Cartaporte, Manifiesto, Declacion
import app_manifiesto
import app_cartaporte
import app_declaracion
#import app_cartaporte.models_doccpi as models_doccpi
#from app_manifiesto.models_docmci import Manifiesto

from app_entidades.models_Entidades import Cliente, Vehiculo, Conductor
from app_usuarios.models import Usuario, Empresa

#-------------------------------------------------------------------
# Class with general Script for handing models in DB and others
#-------------------------------------------------------------------
class Scripts:
	#-------------------------------------------------------------------
	#-- Generate doc number from last doc number saved in DB
	#-------------------------------------------------------------------
#	def generateDocNumber  (DocModel, pais):         # DEPRECATED: Moved to EcuapassDoc
#		num_zeros = 5
#		lastDoc   = DocModel.objects.filter  (pais=pais).exclude  (numero="SUGERIDO").order_by  ("-id").first  ()
#		if lastDoc:
#			lastNumber = Utils.getNumberFromDocNumber  (lastDoc.numero)
#			newNumber  = str  (lastNumber + 1).zfill  (num_zeros)
#		else:
#			newNumber  = str  (1).zfill  (num_zeros)
#
#		docNumber = Utils.getCodigoPaisFromPais  (pais) + newNumber
#		print  (f"+++ docNumber '{docNumber}'")
#		return docNumber

	#-------------------------------------------------------------------
	# Save new DocBaseModel document to DB from formFields
	#-------------------------------------------------------------------
	def saveNewDocToDB  (formFields, docFields, docType, pais, usuario):
		print  (f">>> Guardando '{docType}' nuevo en la BD...")

		FormModel, DocModel = DocUtils.getFormAndDocClass  (docType)
		docNumber           = Scripts.generateDocNumber  (DocModel, pais)      # Fist, generate docNumber based on id of last DocModel row"

		# First, save form model
		formModel           = FormModel  (numero=docNumber, txt00=docNumber)   # Second, save FormModel to get the id"
		for key, value in formFields.items ():                                 # Third, set FormModel values from input form values"
			if key not in ["id", "numero", "txt00"]:
				setattr  (formModel, key, value)
		formModel.save  ()

		# Second, save doc model
		docModel  = DocModel  (id=formModel.id, numero=docNumber, pais=pais, usuario=usuario)
		docModel.setValues  (formModel, docFields, pais, usuario)
		docModel.save  ()

		return formModel, docModel

	#-------------------------------------------------------------------
	# Search a pattern in all fields of a model
	#-------------------------------------------------------------------
	from django.db.models import Q
	def searchModelAllFields  (searchPattern, DOCMODEL):
		queries = Q ()
		for field in DOCMODEL._meta.fields:
			field_name = field.name
			queries |= Q (**{f"{field_name}__icontains": searchPattern})
		
		results = DOCMODEL.objects.filter  (queries)
		return results

	#-------------------------------------------------------------------
	#-- Get cartaporte instance
	#-------------------------------------------------------------------
#	#-- Get cartaporte instance from DocFields
#	def getCartaporteInstanceFromDocFields  (docFields, docType):
#		cartaporteNumber = None
#		try:
#			cartaporteNumber = EcuInfo.getNumeroCartaporte  (docFields, docType)
#			cartaporte       = Scripts.getCartaporteInstanceByNumero  (cartaporteNumber)
#			return cartaporte
#		except: 
#			Utils.printException  (f"+++ ERROR: Obteniendo cartaporte número '{cartaporteNumber}'")
#			return None


	#-- Get cartaporte instance from number
	def getCartaporteInstanceByNumero  (cartaporteNumber):
		try:
			instance = app_cartaporte.models_doccpi.Cartaporte.objects.get  (numero=cartaporteNumber)
			return instance
		except app_cartaporte.models_doccpi.Cartaporte.DoesNotExist:
			Utils.printException (f"+++ No existe cartaporte nro: '{cartaporteNumber}'!")
		except app_cartaporte.models_doccpi.Cartaporte.MultipleObjectsReturned:
			Utils.printException (f"+++ Múltiples instancias de cartaporte nro: '{cartaporteNumber}'!")
		return None
	#-------------------------------------------------------------------
	#-- Get/Save cliente info. Only works for BYZA
	#-- field keys correspond to: remitente, destinatario,...  (Cartaporte)
	#-------------------------------------------------------------------
	def getSaveClienteInstanceFromText  (text, type):
		#clienteInfo  = getClienteInfo  (docKey, docFields)
        #resourcesPath = os.path.join  (settings.BASE_DIR, "resources", "data_ecuapass")
		clienteInfo   = Extractor.getSubjectInfoFromText  (text, type)
		print  (f"+++ clienteInfo::{type} '{clienteInfo}'")
		if Utils.anyLowNone  (clienteInfo):
			return None

		cliente = Scripts.saveClienteInfoToDB  (clienteInfo)
		return cliente

	#-- Get cleinte instance from DB by numeroId
	def getClienteInstanceByNumeroId  (numeroId):
		try:
			instance = Cliente.objects.get  (numeroId=numeroId)
			return  (instance)
		except Cliente.DoesNotExist:
			Utils.printException  (f"Cliente no encontrado con numeroId: '{numeroId}'")
		return None


	#-- Get cleinte instance from DB by nombre
	def getClienteInstanceByNombre  (nombre):
		try:
			#instance = Cliente.objects.get  (nombre=nombre)

			results =  (
				Cliente.objects
				.annotate  (similarity=TrigramSimilarity  ('nombre', nombre))
				.filter  (similarity__gt=0.3)  # Threshold for similarity
				.order_by  ('-similarity')  # Optional: sort by most similar
			)
			if not results:
				return None
			else:
				return  (results [0])
		except Cliente.DoesNotExist:
			print  (f"Cliente no encontrado con nombre: '{nombre}'")
			return None


	#-- Save instance of Cliente with info: id, nombre, direccion, ciudad, pais, tipoId, numeroId
	def saveClienteInfoToDB  (info):
		cliente = None
		try:
			cliente, created = Cliente.objects.get_or_create  (numeroId=info['numeroId'])

			cliente.nombre    = info ["nombre"]
			cliente.direccion = info ["direccion"]
			cliente.ciudad    = info ["ciudad"]
			cliente.pais      = info ["pais"]
			cliente.tipoId    = info ["tipoId"]
			cliente.numeroId  = info ["numeroId"]

			cliente.save  ()
		except:
			Utils.printException  (f"Guardando cliente to DB")
		return cliente

	##----------------------------------------------------------
	##----------------------------------------------------------
	def getVehiculoByPlaca (placa):
		instances = Vehiculo.objects.filter (placa=placa)
		return instances.first () if instances else None

	def getConductorByDocumento (documento):
		instances = Conductor.objects.filter (documento=documento)
		return instances.first () if instances else None

	def getEmpresaByNickname (nickname):
		instances = Empresa.objects.filter (nickname=nickname)
		return instances.first () if instances else None

	def getUsuarioByUsernameEmpresa (username, idEmpresa):
		instances = Usuario.objects.filter (username=username, empresa_id= idEmpresa)
		return instances.first () if instances else None

	def getDocumentById (ModelCLASS, id):
		instances = ModelCLASS.objects.filter (id=id)
		return instances.first () if instances else None
		
	##----------------------------------------------------------
	## ------------------ Functions in models_docmci -------------
	##----------------------------------------------------------
	##----------------------------------------------------------
	## Get / Save Vehiculo info from docFields  (formFields)
	##----------------------------------------------------------
	#def getSaveVehiculoInstance  (docKey, docFields):
	#	vehiculoInfo  = getVehiculoInfo  (docKey, docFields)
	#	if vehiculoInfo:
	#		vehiculo = saveVehiculoInfo  (vehiculoInfo)
	#		return vehiculo
	#	else:
	#		return None
	#
	##-- Get a 'vehiculo' instance from extracted info
	#def getVehiculoInfo  (self, manifiestoInfo, vehicleType):
	#	vehinfo = None
	#	print  ("+++ Tipo vehiculo:", vehicleType)
	#	try:
	#		jsonFieldsPath, runningDir = Utils.createTemporalJson  (docFields)
	#		manifiestoInfo  = ManifiestoInfo  (jsonFieldsPath, runningDir)
	#		vehinfo         = manifiestoInfo.extractVehiculoInfo  (vehicleType)
	#		if any  (value is None for value in vehinfo.values ()):
	#			return None
	#	except:
	#		Utils.printException  (f"Obteniedo info de cliente tipo: '{docKey}'")
	#	return vehinfo
	#
	##-- Save instance of Vehiculo 
	#def saveVehiculoInfo  (vehinfo):
	#	vehiculo = None
	#	try:
	#		vehiculo, created    = Vehiculo.objects.get_or_create  (placa=vehinfo['placa'])
	#		vehiculo.marca       = vehinfo ["marca"]
	#		vehiculo.placa       = vehinfo ["placa"]
	#		vehiculo.pais        = vehinfo ["pais"]
	#		vehiculo.chasis      = vehinfo ["chasis"]
	#		vehiculo.anho        = vehinfo ["anho"]
	#		vehiculo.certificado = vehinfo ["certificado"]
	#		vehiculo.save  ()
	#	except:
	#		Utils.printException  (f"Obteniedo información del vehiculo.")
	#	return vehiculo
	#

	#----------------------------------------------------------
	#-- Return recent cartaportes  (within the past week)
	#----------------------------------------------------------
	def getRecentDocuments  (DOCMODEL, days=5):
		diasRecientes = 7
		daysAgo = timezone.now  () - timedelta  (days=diasRecientes)
		recentDocuments = DOCMODEL.objects.filter  (fecha_emision__gte=daysAgo)
		if not recentDocuments.exists ():
			print  (f"+++ No existen documentos de más de '{days}' dias")

		return recentDocuments

	#----------------------------------------------------------
	#-- Compare whether two instances have the same values for all fields,
	#----------------------------------------------------------
	def areEqualsInstances  (instance1, instance2):
		try:
			if instance1 is None and instance2 is None:
				return True  # Equals
			elif instance1 is None or instance2 is None:
				return False # Different

			if instance1._meta.model != instance2._meta.model:
				return False  # They are not even the same model

			# Compare field values
			for field in instance1._meta.fields:
				value1 = getattr (instance1, field.name)
				value2 = getattr (instance2, field.name)
				if value1 != value2:
					return False  # Return False if any field value is different

			return True  # All fields match
		except:
			return False


	#----------------------------------------------------------
	# Print all instances of a class or all objects if no class specified.
	#----------------------------------------------------------

	def printAllInstances (instances, show_attributes=False, max_attributes=5):
		import gc
		import inspect
		"""
			instances: instances to show
			show_attributes: Whether to display object attributes
			max_attributes: Maximum number of attributes to display
		"""
		all_objects = gc.get_objects ()

		print (f"Total: {len (instances)}")
		print ("-" * 50)

		for i, obj in enumerate (instances, 1):
			print (f"{i}. {obj}  (id: {id (obj)})")

			if show_attributes:
				try:
					# Get attributes  (excluding magic methods)
					attrs = {k: v for k, v in vars (obj).items ()
							if not k.startswith ('__')}

					if attrs:
						print (f"   Attributes:")
						for attr_name, attr_value in list (attrs.items ())[:max_attributes]:
							print (f"     {attr_name}: {repr (attr_value)[:100]}{'...' if len (repr (attr_value)) > 100 else ''}")
						if len (attrs) > max_attributes:
							print (f"     ... and {len (attrs) - max_attributes} more attributes")
					print ()
				except Exception as e:
					print (f"   [Could not access attributes: {e}]")
					print ()
