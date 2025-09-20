# core/tenant_context.py
"""
Stores the current empresa for the lifetime of a request.
"""
from contextvars import ContextVar

_current_empresa = ContextVar ("current_empresa", default=None)

def set_current_empresa (empresa):
    _current_empresa.set (empresa)

def get_current_empresa ():
    empresa = _current_empresa.get ()
    if not empresa:
        raise RuntimeError ("Empresa  (tenant) not set in context")
    return empresa

