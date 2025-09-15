"""
Conatins all general entities (models) used by the three ECUAPASS documents
"""

from django.db import models
from django.urls import reverse  # To generate URLS by reversing URL patterns
from django.db.models import Q

#--------------------------------------------------------------------
# Base model for entities models (Vehiculo, Conductor, Cliente)
#--------------------------------------------------------------------
class DocEntity (models.Model):
	class Meta:
		abstract = True

	#-------------------------------------------------------------------
	# Methods for special column "Acciones" when listing documents
	#-------------------------------------------------------------------
	#-- Returns document type as class model name ("cartaporte", "manifiesto", "declaracion")
	def getDocType(self):
		return self.__class__.__name__.lower ()

	def get_link_editar(self):
		url     = f"{self.getDocType()}-editar"
		return reverse (url, args=[self.pk])

	def get_link_eliminar(self):
		url     = f"{self.getDocType()}-eliminar"
		return reverse (url, args=[self.pk])

	#-- Search a pattern in all fields of a model
	#-- Overwritten in some child classes
	def searchModelAllFields (searchPattern, DOCMODEL):
		queries = Q()
		for field in DOCMODEL._meta.fields:
			field_name = field.name
			queries |= Q(**{f"{field_name}__icontains": searchPattern})
		
		results = DOCMODEL.objects.filter (queries)
		return results


#--------------------------------------------------------------------
# Model Cliente
#--------------------------------------------------------------------
class Cliente (DocEntity):
	class Meta:
		db_table = "cliente"

	numeroId     = models.CharField (max_length=30)
	nombre       = models.CharField (max_length=100)
	direccion    = models.CharField (max_length=100)
	ciudad       = models.CharField (max_length=50)
	pais         = models.CharField (max_length=20)
	tipoId       = models.CharField (max_length=20)

	def get_absolute_url(self):
		"""Returns the url to access a particular language instance."""
		return reverse('cliente-detail', args=[str(self.id)])

	#-- Search a pattern in all fields of the model
	def searchModelAllFields (self, searchPattern):
		return DocEntity.searchModelAllFields (searchPattern, Cliente)

	def __str__ (self):
		return f"{self.nombre} {self.ciudad}-{self.pais}"

	#-- Format info as used in form document
	def toDocFormat (self):
		text = f"{self.nombre}\n{self.direccion}\n{self.tipoId}:{self.numeroId}.  {self.ciudad}-{self.pais}"
		return text
	
#--------------------------------------------------------------------
# Model Conductor
#--------------------------------------------------------------------
class Conductor (DocEntity):
	class Meta:
		db_table = "conductor"
		verbose_name_plural = "Conductores"

	paises  = [("COLOMBIA","COLOMBIA"),("ECUADOR", "ECUADOR"),("PERU","PERU"),("OTRO","OTRO")]
	tiposId = ["RUC", "CEDULA DE IDENTIDAD", "CATASTRO", "PASAPORTE", "OTROS"]

	documento        = models.CharField (max_length=20)
	nombre           = models.CharField (max_length=100, null=True, blank=True) 
	pais             = models.CharField (max_length=50, null=True, blank=True, choices=paises, default="COLOMBIA")
	licencia         = models.CharField (max_length=50, null=True, blank=True)
	tipoDoc          = models.CharField (max_length=50, null=True, blank=True, default="CEDULA DE IDENTIDAD")
	fecha_nacimiento  = models.CharField (max_length=50, null=True, blank=True)
	sexo             = models.CharField (max_length=20, null=True, blank=True)
	auxiliar         = models.OneToOneField ('self', null=True, blank=True, 
										  on_delete=models.SET_NULL, related_name='conductor_principal')

	#-- Returns the url to access a particular genre instance.
	def get_absolute_url(self):
		return reverse('conductor-detail', args=[str(self.id)])

	#-- Search a pattern in all fields of the model
	def searchModelAllFields (self, searchPattern):
		results = Conductor.objects.filter(
			Q (documento__icontains=searchPattern) | 
			Q (nombre__icontains=searchPattern) | 
			Q (pais__icontains=searchPattern))
		return results

	def __str__ (self):
		return f"{self.documento}, {self.nombre}"

#--------------------------------------------------------------------
# Vehiculo entity
#--------------------------------------------------------------------
class Vehiculo (DocEntity):
	class Meta:
		db_table = "vehiculo"

	placa       = models.CharField (max_length=50)
	marca       = models.CharField (max_length=100, null=True, blank=True) 
	pais        = models.CharField (max_length=20, null=True, blank=True)
	chasis      = models.CharField (max_length=50, null=True, blank=True)
	anho        = models.CharField (max_length=20, null=True, blank=True)
	certificado = models.CharField (max_length=20, null=True, blank=True)
	tipo        = models.CharField (max_length=20, null=True, blank=True)
	conductor   = models.ForeignKey (Conductor, null=True, blank=True, 
								  on_delete=models.SET_NULL, related_name="vehiculos")
	remolque    = models.ForeignKey ('self', null=True, blank=True, 
						on_delete=models.SET_NULL, related_name='vehiculos')

	def get_absolute_url(self):
		"""Returns the url to access a particular language instance."""
		return reverse('vehiculo-detail', args=[str(self.id)])

	#-- Search a pattern in all fields of the model
	def searchModelAllFields (self, searchPattern):
		results = Vehiculo.objects.filter(
			Q (placa__icontains=searchPattern) | 
			Q (marca__icontains=searchPattern) | 
			Q (conductor__nombre__icontains=searchPattern))
		return results

	def __str__ (self):
		return f"{self.placa}, {self.marca}"
	
