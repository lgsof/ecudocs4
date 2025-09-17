from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from django.conf import settings

class UsuarioManager (BaseUserManager):
	def create_user (self, username, email, password=None, **extra_fields):
		if not email:
			raise ValueError ('El correo es obligatorio')

		email = self.normalize_email (email)
		user  = self.model (username=username.strip (), email=email, **extra_fields)
		user.set_password (password)
		user.save (using=self._db)
		return user

	def create_superuser (self, username, email, password=None, **extra_fields):
		extra_fields.setdefault ('is_staff', True)
		extra_fields.setdefault ('is_superuser', True)
		extra_fields.setdefault ('perfil', 'director')

		if extra_fields.get ('is_staff') is not True:
			raise ValueError ('Superuser must have is_staff=True.')
		if extra_fields.get ('is_superuser') is not True:
			raise ValueError ('Superuser must have is_superuser=True.')

		return self.create_user (username, email, password, **extra_fields)


#--------------------------------------------------------------------	
#--------------------------------------------------------------------	
from django.utils import timezone
class Empresa (models.Model):
	nickname       = models.SlugField (unique=True, help_text="Ej: 'byza', 'logitrans'")
	nombre	       = models.CharField (max_length=100)
	activo	       = models.BooleanField (default=True)
	fecha_creacion = models.DateTimeField (auto_now_add=True)

	permiso        = models.CharField (max_length=20, null=True, blank=True)
	nit		       = models.CharField (max_length=20, null=True, blank=True)
	direccion      = models.CharField (max_length=200, null=True, blank=True)
	telefono       = models.CharField (max_length=50, null=True, blank=True)
	email	       = models.EmailField (null=True, blank=True)

	class Meta:
		db_table = 'empresa'

	def __str__ (self):
		return f"{self.nickname} : {self.nombre}"

	def getValues (self):
		raise Exception ("Error: Función aun no implementada")


#--------------------------------------------------------------------	
#--------------------------------------------------------------------	
class Usuario (AbstractUser):
	class Pais (models.TextChoices):
		ECUADOR  = 'ECUADOR',  'Ecuador'
		COLOMBIA = 'COLOMBIA', 'Colombia'
		PERU	 = 'PERU',	   'Perú'
		TODOS	 = 'TODOS',    'Todos'

	class Perfil (models.TextChoices):
		EXTERNO		= 'externo',	 'Externo'
		FUNCIONARIO = 'funcionario', 'Funcionario'
		DIRECTOR	= 'director',	 'Director'

	class Meta:
		db_table = 'usuario'
		indexes = [
			models.Index (fields=['pais']),
			models.Index (fields=['perfil']),
		]
		# Si quieres unicidad por empresa  (multi-tenant), lee la nota al final.

	# Campos extra a los del AbstractUser
	nombre	= models.CharField (_ ('nombre'), max_length=100, blank=True)
	empresa = models.ForeignKey ('Empresa', on_delete=models.CASCADE, 
								null=True, blank=True, related_name='usuarios')
	pais	= models.CharField (max_length=20, choices=Pais.choices,
							   default=Pais.TODOS)
	perfil	= models.CharField (max_length=20, choices=Perfil.choices,
							   default=Perfil.EXTERNO)

	# Override para hacer email único a nivel global  (opcional pero recomendado)
	email = models.EmailField (_ ('correo electrónico'), unique=True)

	# Contadores
	nro_docs_creados   = models.PositiveIntegerField (default=0)
	nro_docs_asignados = models.PositiveIntegerField (default=0)

	# Manager por defecto basta si `username` sigue siendo el login
	objects = UserManager ()

	# Helpers en vez de 3 booleanos almacenados
	@property
	def es_director (self): return self.perfil == self.Perfil.DIRECTOR

	@property
	def es_funcionario (self): return self.perfil == self.Perfil.FUNCIONARIO

	@property
	def es_externo (self): return self.perfil == self.Perfil.EXTERNO

	# En listas/administración
	def __str__ (self):
		return self.get_full_name () or self.username

	# Enlaces “Acciones”  (si los usas en templates)
	def get_link_actualizar (self):
		return reverse ('actualizar', args=[self.pk])

	def get_link_eliminar (self):
		return reverse ('eliminar', args=[self.pk])

