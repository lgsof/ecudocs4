"""
Script for handling subdomains in Django
"""

# app_main/hosts.py
from django_hosts import patterns, host

host_patterns = patterns('',
    host(r'www', 'app_main.urls',  name='www'),        # www.ecuapassdocs.app → urls públicas (o landing)
    host(r'(?!www).*', 'app_main.urls', name='tenant') # cualquier otro subdominio → mismas urls (middleware decide)
)

