# core/middleware.py
"""
Resolves the tenant from the subdomain and sets it on request and the context.
"""
from django.http import HttpResponseBadRequest
from django.conf import settings

from core.tenant_context import set_current_empresa
from app_usuarios.models import Empresa  # adjust if your app label is different

def _get_host_without_port (request):
    return request.get_host ().split (":")[0]

def _extract_subdomain (host):
    # e.g. byza.ecuapassdocs.app -> "byza"; localhost -> None; byza.lvh.me -> "byza"
    parts = host.split (".")
    if len (parts) <= 1:
        return None
    # treat lvh.me and localhost variants as having subdomain
    if host.endswith (".lvh.me") or host.endswith (".localhost"):
        return parts[0]
    # typical production: sub.domain.tld -> sub
    return parts[0] if len (parts) >= 3 else None

def _empresa_from_dev_map (sub):
    # Optional dev mapping in settings: {"byza": 1, "nta": 2}
    tenant_map = getattr (settings, "DEV_TENANT_MAP", None)
    if tenant_map and sub in tenant_map:
        try:
            return Empresa.objects.get (pk=tenant_map[sub])
        except Empresa.DoesNotExist:
            return None
    return None

def _empresa_by_nombre (sub):
    # As a no-migration fallback, allow Empresa.nombre == sub  (case-insensitive)
    try:
        return Empresa.objects.get (nickname__iexact=sub)
    except Empresa.DoesNotExist:
        return None

class SubdomainTenantMiddleware:
    """
    Resolve tenant from subdomain  (dev-friendly, no migrations required).
    Order:
      1) settings.DEV_TENANT_MAP  (subdomain -> empresa_id)
      2) Empresa.nombre == subdomain  (iexact)
    """
    def __init__ (self, get_response):
        self.get_response = get_response

    def __call__ (self, request):
        host = _get_host_without_port (request)
        sub = _extract_subdomain (host)
        if not sub:
            return HttpResponseBadRequest ("Missing tenant subdomain.")

        # 1) Try explicit dev map
        empresa = _empresa_from_dev_map (sub)
        # 2) Fallback: match by Empresa.nombre
        if not empresa:
            empresa = _empresa_by_nombre (sub)

        if not empresa:
            return HttpResponseBadRequest (f"Unknown tenant for subdomain '{sub}'.")

        # Make tenant available everywhere
        request.empresa = empresa
        set_current_empresa (empresa)

        return self.get_response (request)

