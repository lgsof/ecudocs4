# core/managers.py

"""
An ORM manager that auto-filters queries to the current tenant.
"""
from django.db import models
from core.tenant_context import get_current_empresa

class TenantManager (models.Manager):
    def get_queryset (self):
        try:
            empresa = get_current_empresa ()
            return super ().get_queryset ().filter (empresa=empresa)
        except RuntimeError:
            # Allows manage.py commands / places with no tenant context
            return super ().get_queryset ()

