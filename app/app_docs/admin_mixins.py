from django.contrib import admin
# app_core/mixins/tenant_mixins.py
from django.http import Http404
from django.db.models import Model
from django.views.generic.edit import ModelFormMixin

# For admin multi-tenant support
class EmpresaFilterAdminMixin:
    """
    Limita el queryset a la empresa del usuario actual (del request.empresa),
    y asigna esa empresa al guardar nuevos registros.
    """

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(request, "empresa") and request.empresa:
            return qs.filter(empresa=request.empresa)
        return qs.none()  # seguridad: nada si no hay empresa en request

    def save_model(self, request, obj, form, change):
        if hasattr(request, "empresa") and request.empresa:
            obj.empresa = request.empresa
        super().save_model(request, obj, form, change)

#--------------------------------------------------------------------
#
#--------------------------------------------------------------------
class TenantGuardMixin:
    """
    Ensures request.empresa exists. Use on any view that needs a tenant.
    """
    def _require_empresa(self):
        req = getattr(self, "request", None)
        if not req or not getattr(req, "empresa", None):
            raise Http404("Empresa not found")

    def dispatch(self, request, *args, **kwargs):
        self._require_empresa()
        return super().dispatch(request, *args, **kwargs)


class TenantQuerysetMixin:
    """
    Filters queryset by tenant. Works with ListView/DetailView/Update/Delete.
    - Set tenant_field if your FK is not named 'empresa'.
    """
    tenant_field = "empresa"
    model: type[Model] | None = None

    def get_tenant_value(self):
        return self.request.empresa

    def get_base_queryset(self):
        # Prefer parent's get_queryset if it exists, else model._default_manager
        if hasattr(super(), "get_queryset"):
            return super().get_queryset()  # type: ignore[misc]
        if self.model is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} must define .model or override get_queryset()"
            )
        return self.model._default_manager.all()

    def get_queryset(self):
        # Guard first
        if not getattr(self.request, "empresa", None):
            raise Http404("Empresa not found")

        qs = self.get_base_queryset()
        # If the model doesn't have tenant_field, fail loudly to catch misconfigs
        if self.tenant_field not in {f.name for f in qs.model._meta.fields}:
            raise ImproperlyConfigured(
                f"{qs.model.__name__} lacks '{self.tenant_field}' field."
            )
        return qs.filter(**{self.tenant_field: self.get_tenant_value()})


class TenantCreateMixin(ModelFormMixin):
    """
    On create, auto-assigns tenant FK (empresa) before save.
    Use on CreateView (and optionally on UpdateView if you want to reassert).
    """
    tenant_field = "empresa"

    def form_valid(self, form):
        if not getattr(self.request, "empresa", None):
            raise Http404("Empresa not found")
        # Only set if the field exists on the instance
        if hasattr(form.instance, self.tenant_field):
            setattr(form.instance, self.tenant_field, self.request.empresa)
        return super().form_valid(form)

