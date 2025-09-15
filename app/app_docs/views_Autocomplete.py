
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
		days = 30
		try:
			# Get cartaporte docs from query
			query = request.POST.get ('query', '')

			cartaportes     = Scripts.getRecentDocuments (Cartaporte, days)
			docsCartaportes = [model for model in cartaportes]
			print (f"\n+++ '{docsCartaportes=}'")

			for i, doc in enumerate (docsCartaportes):
				print (f"\n+++ '{doc.printInfo()=}'")
				itemLine = f"{i}. {doc.getTxt ('txt00')}"
				itemText = "%s||%s||%s||%s||%s||%s||%s||%s||%s||%s||%s||%s" % ( 
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

				newOption = {"itemLine" : itemLine, "itemText" : itemText}
				itemOptions.append (newOption)
		except Cartaporte.DoesNotExist:
			print (f"+++ No existe cartaportes desde hace '{dias}'  ")
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
			itemLine = f"{i}. {option['placa']}-{option['pais']}"
			itemText = f"{option['placa']}-{option['pais']}"
			newOption = {"itemLine" : itemLine, "itemText" : itemText}
			itemOptions.append (newOption)
		
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
			itemLine = f"{i}. {vehiculo.placa}-{vehiculo.pais}"
			#-- Vehiculo
			itemText = "%s||%s||%s||%s" % (vehiculo.marca, vehiculo.anho, 
			            f"{vehiculo.placa}-{vehiculo.pais}", vehiculo.chasis)
			#-- Remolque
			remolque = vehiculo.remolque
			if remolque:
				itemText += "||%s||%s||%s||%s" % (remolque.marca, remolque.anho, 
							f"{remolque.placa}-{remolque.pais}", remolque.chasis)
			else:
				itemText += "||None||None||None||None"

			#-- Conductor
			conductor = vehiculo.conductor
			if conductor:
				itemText += "||%s||%s||%s||%s" % (conductor.nombre, conductor.documento, 
							conductor.pais, conductor.licencia)
			else:
				itemText += "||None||None||None||None"

			newOption = {"itemLine" : itemLine, "itemText" : itemText}
			items.append (newOption)

		return JsonResponse (items, safe=False)

#--------------------------------------------------------------------
# Show placa-pais options from Vehiculo model
# Used in declaracion form
#--------------------------------------------------------------------
class ManifiestoOptionsView (View):
	@method_decorator(csrf_protect)
	def post (self, request, *args, **kwargs):
		print (f"+++ DEBUG: ManifiestoOptionsView:POST '{request}'")
		itemOptions = []
		try:
			# Get cartaporte docs from query
			query = request.POST.get ('query', '')

			manifiestos  = Scripts.getRecentDocuments (Manifiesto)
			if not manifiestos.exists():
				manifiestos = Manifiesto.objects.filter (numero__startswith=query, fecha_emision=current_date)

			docsManifiestos = [model.documento.__dict__ for model in manifiestos]

			for i, doc in enumerate (docsManifiestos):
				itemLine = f"{i}. {doc['numero']}"
				itemText = "%s||%s||%s||%s||%s||%s||%s||%s||%s||%s||%s||%s||%s" % ( 
							doc ['numero'],  # 
							doc ["txt26"],   # Contenedores 
							doc ["txt27"],   # Precintos
							doc ["txt28"],   # Cartaporte
							doc ["txt29"],   # Descripcion
							doc ["txt30"],   # Cantidad
							doc ["txt31"],   # Embalaje
							doc ["txt32_1"], # Peso bruto
							doc ["txt32_3"], # Peso neto
							doc ["txt33_1"], # Otras medidas
							doc ["txt34"],   # Incoterms
							doc ["txt37"],   # PaisAduana-cruce
							doc ["txt40"])   # FechaEmision

				print (f"+++ DEBUG: itemText '{itemText}'")
				newOption = {"itemLine" : itemLine, "itemText" : itemText}
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
			itemLine = f"{i}. {option['nombre']}"
			itemText = "%s||%s||%s||%s||%s" % (option["nombre"], option["documento"], 
			           option["pais"], option ["licencia"], option ["fecha_nacimiento"])
			newOption = {"itemLine" : itemLine, "itemText" : itemText}
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
			itemLine = f"{i}. {item}"
			itemText = f"{item}. {currentDate}" if currentDate else f"{item}"
			newItem = {"itemLine" : itemLine, "itemText" : itemText}
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
			itemLine = f"{i}. {option['nombre']}"
			itemText = "%s\n%s\n%s-%s. %s:%s" % (
			              option ["nombre"], option ["direccion"], 
						  option ["ciudad"], option ["pais"],
						  option ["tipoId"], option ["numeroId"])

			newOption = {"itemLine" : itemLine, "itemText" : itemText}
			itemOptions.append (newOption)

		return JsonResponse (itemOptions, safe=False)


