
import re, datetime

# For CSRF protection
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from django.views import View
from django.http import JsonResponse

from ecuapassdocs.utils.resourceloader import ResourceLoader 
from ecuapassdocs.info.ecuapass_utils import Utils

from ecuapassdocs.utils.models_scripts import Scripts
from app_cartaporte.models_doccpi import Cartaporte
from app_manifiesto.models_docmci import Manifiesto

from app_entidades.models_Entidades import Vehiculo, Conductor, Cliente

#--------------------------------------------------------------------
# Show all 'cartaportes' from current date (selected in manifiesto)
# Fill from with "mercancia" info (cartaporte, descripcion, ..., totals
# It doesn't totalize peso "bruto", "neto", and "otras"
#--------------------------------------------------------------------
class CartaporteOptionsView (View):
	@method_decorator(csrf_protect)
	def post (self, request, *args, **kwargs):
		itemOptions = []
		days = 5
		try:
			# Get cartaporte docs from query
			query = request.POST.get ('query', '')

			cartaportes     = Scripts.getRecentDocuments (Cartaporte, days)
			docsCartaportes = [model for model in cartaportes]

			for i, doc in enumerate (docsCartaportes):
				itemLabel = doc.getTxt ('txt00')
				itemValue = "%s||%s||%s||%s||%s||%s||%s||%s||%s||%s||%s||%s" % ( 
							doc.getTxt ('txt00'),  # Cartaporte
							doc.getTxt ("txt12"),   # Descripcion 
							doc.getTxt ("txt10"),   # Cantidad
							doc.getTxt ("txt11"),   # Marca
							doc.getTxt ("txt13_2"), # Peso bruto
							doc.getTxt ("txt13_1"), # Peso neto
							doc.getTxt ("txt15"),   # Otras unidades
							re.sub (r'[\r\n]+\s*', '. ', doc.getTxt ("txt16")), # INCONTERMS
							doc.getTxt ("txt13_2"), # Peso bruto total
							doc.getTxt ("txt13_1"), # Peso neto total
							doc.getTxt ("txt15"),  # Otras unidades total
							doc.getTxt ("txt19")   # Fecha emision
				)
				itemOptions.append ({"label":itemLabel, "value":itemLabel, "info":itemValue})
		except Cartaporte.DoesNotExist:
			print (f"+++ No existen cartaportes desde hace '{dias}'  ")
		except:
			Utils.printException (">>> Excepcion obteniendo opciones de cartaportes")
			
		return JsonResponse (itemOptions, safe=False)

#--------------------------------------------------------------------
# Show Manifiesto number from Manifiesto model
#--------------------------------------------------------------------
class PlacaOptionsView (View):
	@method_decorator(csrf_protect)
	def post (self, request, *args, **kwargs):
		query   = request.POST.get('query', '')
		options = Vehiculo.objects.filter (placa__istartswith=query).values ('placa','pais')

		itemOptions = []
		for i, option in enumerate (options):
			itemLabel = f"{option['placa']}-{option['pais']}"
			itemOptions.append ({"label" : itemLabel, "value" : itemLabel, "info":itemLabel})
		
		return JsonResponse (itemOptions, safe=False)

#--------------------------------------------------------------------
# Show options when user types in "input_placaPais"
#--------------------------------------------------------------------
class VehiculoOptionsView (View):
	@method_decorator(csrf_protect)
	def post (self, request, *args, **kwargs):
		query = request.POST.get('query', '')

		#-- Vehiculo
		vehiculos = Vehiculo.objects.filter (placa__istartswith=query)
		items = []
		for i, vehiculo in enumerate (vehiculos):
			itemLabel = f"{vehiculo.placa}-{vehiculo.pais}"
			#-- Vehiculo
			itemValue = "%s||%s||%s||%s" % (f"{vehiculo.placa}-{vehiculo.pais}", 
						vehiculo.chasis, vehiculo.marca, vehiculo.anho) 
			#-- Remolque
			remolque = vehiculo.remolque
			if remolque:
				itemValue += "||%s||%s||%s||%s" % (f"{remolque.placa}-{remolque.pais}", 
						remolque.chasis, remolque.marca, remolque.anho)
			else:
				itemValue += "||None||None||None||None"

			#-- Conductor
			conductor = vehiculo.conductor
			if conductor:
				itemValue += "||%s||%s||%s||%s" % (conductor.nombre, conductor.documento, 
							conductor.pais, conductor.licencia)
			else:
				itemValue += "||None||None||None||None"

			newOption = {"label":itemLabel, "value":itemLabel, "info":itemValue}
			items.append (newOption)

		return JsonResponse (items, safe=False)

#--------------------------------------------------------------------
# Show placa-pais options from Vehiculo model
# Used in declaracion form
#--------------------------------------------------------------------
class ManifiestoOptionsView (View):
	@method_decorator(csrf_protect)
	def post (self, request, *args, **kwargs):
		itemOptions = []
		try:
			# Get cartaporte docs from query
			query = request.POST.get ('query', '')

			manifiestos  = Scripts.getRecentDocuments (Manifiesto)
			docsManifiestos = [model for model in manifiestos]

			for i, doc in enumerate (docsManifiestos):
				itemLabel = doc.getTxt ('txt00')
				itemValue = "%s||%s||%s||%s||%s||%s||%s||%s||%s||%s||%s||%s||%s" % ( 
							doc.getTxt ('txt00'),  # 
							doc.getTxt ("txt26"),   # Contenedores 
							doc.getTxt ("txt27"),   # Precintos
							doc.getTxt ("txt28"),   # Cartaporte
							doc.getTxt ("txt29"),   # Descripcion
							doc.getTxt ("txt30"),   # Cantidad
							doc.getTxt ("txt31"),   # Embalaje
							doc.getTxt ("txt32_1"), # Peso bruto
							doc.getTxt ("txt32_3"), # Peso neto
							doc.getTxt ("txt33_1"), # Otras medidas
							doc.getTxt ("txt34"),   # Incoterms
							doc.getTxt ("txt37"),   # PaisAduana-cruce
							doc.getTxt ("txt40"))   # FechaEmision

				newOption = {"label":itemLabel, "value":itemLabel, "info" : itemValue}
				itemOptions.append (newOption)
		except:
			Utils.printException (">>> Excepcion obteniendo opciones de manifiestos")
			
		return JsonResponse (itemOptions, safe=False)

#--------------------------------------------------------------------
# Show options when user types in "input_placaPais"
#--------------------------------------------------------------------
class ConductorOptionsView (View):
	#@method_decorator(csrf_protect)
	def post (self, request, *args, **kwargs):
		query = request.POST.get('query', '')
		options = Conductor.objects.filter (nombre__istartswith=query).values()

		itemOptions = []
		for i, option in enumerate (options):
			option    = Utils.toString (option)
			itemLabel = option['nombre']
			itemValue = "%s||%s||%s||%s||%s" % (option["nombre"], option["documento"], 
			           option["pais"], option ["licencia"], option ["fecha_nacimiento"])
			newOption = {"label":itemLabel, "value":itemLabel, "info":itemValue}
			itemOptions.append (newOption)
		return JsonResponse (itemOptions, safe=False)

#--------------------------------------------------------------------
# Options for autocomplete for "Ciudad-Pais. Fecha"
#--------------------------------------------------------------------
class CiudadPaisOptionsView (View):
	#@method_decorator(csrf_protect)
	def post (self, request, *args, **kwargs):
		query = request.POST.get('query', '')
		ciudadesPaises = self.getCiudadesPaisesFromQuery (query)

		itemOptions = []
		currentDate = self.getFormatedCurrentDate ()
		for i, item in enumerate (ciudadesPaises):
			itemLabel = item
			itemValue = f"{item}. {currentDate}" if currentDate else f"{item}"
			newItem = {"label":itemLabel, "value":itemLabel, "info" : itemValue}
			itemOptions.append (newItem)

		return JsonResponse (itemOptions, safe=False)

	#-- Return empty string for date
	def getFormatedCurrentDate (self):
		return ""

	def getCiudadesPaisesFromQuery (self, query):
		ciudadesPaises = ResourceLoader.loadText ("data_common", "ciudades_paises_principales.txt")
		ciudadesPaises = [x.upper().strip() for x in ciudadesPaises if x.upper().startswith (query)]
		return ciudadesPaises


class CiudadPaisFechaOptionsView (CiudadPaisOptionsView):
	#-- Return formated string for date
	def getFormatedCurrentDate (self):
		from datetime import datetime
		spanish_months = { "January": "ENERO", "February": "FEBRERO", "March": "MARZO", "April": "ABRIL",
			"May": "MAYO", "June": "JUNIO", "July": "JULIO", "August": "AGOSTO", "September": "SEPTIEMBRE",
			"October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE"
		}
		current_time = datetime.now()

		# Format the current time as "YEAR-MONTH-DAY"
		formatted_time = current_time.strftime("%d-{}-%Y").format(spanish_months[current_time.strftime("%B")])

		return (formatted_time)

#--------------------------------------------------------------------
#-- ClienteOptionsView
#--------------------------------------------------------------------
class ClienteOptionsView (View):
	#@method_decorator(csrf_protect)
	def post (self, request, *args, **kwargs):
		query = request.POST.get('query', '')
		options = Cliente.objects.filter (nombre__istartswith=query).values()

		itemOptions = []
		for i, option in enumerate (options):
			itemLabel = f"{option['nombre']}"
			itemValue = "%s\n%s\n%s-%s. %s:%s" % (
			              option ["nombre"], option ["direccion"], 
						  option ["ciudad"], option ["pais"],
						  option ["tipoId"], option ["numeroId"])

			newOption = {"label":itemLabel, "value":itemLabel, "info":itemValue}
			itemOptions.append (newOption)

		return JsonResponse (itemOptions, safe=False)


