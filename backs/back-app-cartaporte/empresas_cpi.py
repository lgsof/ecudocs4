"""
Map cartaporte info classes to specific "empresas" (URL subdomains)
"""

from ecuapassdocs.info.ecuapass_info_BYZA import Cartaporte_BYZA
from ecuapassdocs.info.ecuapass_info_LOGITRANS import Cartaporte_LOGITRANS
from ecuapassdocs.info.ecuapass_info_cartaporte import CartaporteInfo

EMPRESA_CLASSES = {
	"byza" : Cartaporte_BYZA,
	"logitrans" : Cartaporte_LOGITRANS
}

def getDocInfoClassForEmpresa (subdomain):
	return EMPRESA_CLASSES.get (subdomain, CartaporteInfo)


