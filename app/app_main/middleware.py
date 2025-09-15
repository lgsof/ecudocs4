# app_cartaporte/middleware.py
from urllib.parse import urlparse
from django.conf import settings
from django.http import HttpResponseRedirect
from app_usuarios.models import Empresa

SAFE_PREFIXES =  ("/admin", "/onboarding")  # rutas permitidas sin subdominio

class EmpresaMiddleware:
	def __init__ (self, get_response):
		self.get_response = get_response
		self.public_url = getattr (settings, "SITE_DEFAULT_URL", "https://ecuapassdocs.app")
		self.public_host = urlparse (self.public_url).hostname or "ecuapassdocs.app"

	def __call__ (self, request):
		host = request.get_host ().split (":")[0].lower ()
		path = request.path
		parts = host.split (".")

		# Deja pasar admin/onboarding sin subdominio
		if path.startswith (SAFE_PREFIXES):
			request.empresa = None
			return self.get_response (request)

		# Resolver subdominio  (soporta *.localhost)
		subdomain = None
		if host == "localhost":
			subdomain = None
		elif host.endswith (".localhost"):
			subdomain = parts[0]  # p.ej. byza.localhost -> byza
		else:
			if len (parts) >= 3:
				subdomain = parts[0]

		# Evitar loops en el host público
		if host == self.public_host:
			request.empresa = None
			return self.get_response (request)

		# Redirigir a sitio público si no hay subdominio o es 'www'
		if subdomain is None or subdomain == "www":
			return HttpResponseRedirect (self.public_url)

		# Resolver empresa por subdominio; si no existe, redirigir a público
		try:
			empresa         = Empresa.objects.get (nickname=subdomain, activo=True)
			request.empresa = empresa
			print  (f"+++ request.empresa: '{empresa.nickname}'")
		except Empresa.DoesNotExist:
			return HttpResponseRedirect (self.public_url)

		return self.get_response (request)

