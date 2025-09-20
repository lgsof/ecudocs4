# core/mixins.py
# core/views_mixins.py
"""
Different mixins to handel Multi-Tenants
"""

from django.http import HttpResponseBadRequest
from django.core.exceptions import ImproperlyConfigured
from django.views.generic.edit import ModelFormMixin
from django.db import models

from core.tenant_context import get_current_empresa

# Decorator version for FBVs like docView()."""
def require_tenant(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        try:
            request.empresa = get_current_empresa()
        except RuntimeError:
            return HttpResponseBadRequest("Tenant missing")
        return view_func(request, *args, **kwargs)
    return _wrapped

#--------------------------------------------------------------------
# Optional convenience mixin to auto-assign empresa on save.
#--------------------------------------------------------------------
class TenantOwnedModel (models.Model):
    """
    Abstract base class: ensures 'empresa' is set on create/save.
    Your models can inherit from this, or you can skip it if you prefer.
    """
    class Meta:
        abstract = True

    def save (self, *args, **kwargs):
        if hasattr (self, "empresa_id") and not self.empresa_id:
            try:
                self.empresa = get_current_empresa ()
            except RuntimeError:
                pass  # Allow fixtures / shell without tenant context
        super ().save (*args, **kwargs)

#--------------------------------------------------------------------
# Fail fast if no tenant was resolved by middleware.
#--------------------------------------------------------------------
class TenantRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        try:
            get_current_empresa()
        except RuntimeError:
            return HttpResponseBadRequest("Tenant missing")
        return super().dispatch(request, *args, **kwargs)

#--------------------------------------------------------------------
# Unified queryset filter by tenant for List/Detail/Update/Delete CBVs.
# Set tenant_field if your FK isn't named 'empresa'.
#--------------------------------------------------------------------
class TenantQuerysetMixin:
    """
    """
    tenant_field = "empresa"
    model = None
    _has_tenant_field_cache = None  # per-class cache

    def _get_tenant(self):
        # Prefer request.empresa set by middleware; fallback to context var
        tenant = getattr(self.request, "empresa", None)
        if tenant:
            return tenant
        return get_current_empresa()  # may raise RuntimeError if truly missing

    def _get_base_queryset(self):
        # Respect upstream overrides; otherwise require .model
        if hasattr(super(), "get_queryset"):
            return super().get_queryset()  # type: ignore
        if self.model is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} must define .model or override get_queryset()."
            )
        return self.model._default_manager.all()

    def _ensure_tenant_field(self, model_cls):
        if self._has_tenant_field_cache is not None:
            return self._has_tenant_field_cache
        try:
            model_cls._meta.get_field(self.tenant_field)
            self._has_tenant_field_cache = True
        except Exception:
            self._has_tenant_field_cache = False
        return self._has_tenant_field_cache

    def get_queryset(self):
        try:
            tenant = self._get_tenant()
        except RuntimeError:
            # No tenant in context (e.g., tests, misconfigured request)
            return self.model._default_manager.none() if self.model else super().get_queryset().none()  # type: ignore

        qs = self._get_base_queryset()
        if not self._ensure_tenant_field(qs.model):
            raise ImproperlyConfigured(
                f"{qs.model.__name__} lacks tenant field '{self.tenant_field}'."
            )
        return qs.filter(**{self.tenant_field: tenant})

#-- Auto-assign current tenant on create/update if missing.
class TenantAssignOnSaveMixin(ModelFormMixin):
    tenant_field = "empresa"

    def form_valid(self, form):
        instance = form.instance
        # Only set if field exists and isn't set yet
        if hasattr(instance, f"{self.tenant_field}_id") and not getattr(instance, f"{self.tenant_field}_id"):
            try:
                setattr(instance, self.tenant_field, get_current_empresa())
            except RuntimeError:
                return HttpResponseBadRequest("Tenant missing")
        return super().form_valid(form)

