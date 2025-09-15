
# For autoupdate listing

# app_cartaporte/views_cpi.py  (or your listing views module)
from django.shortcuts import render
from django_tables2 import RequestConfig
from app_cartaporte.models_doccpi import Cartaporte
from app_cartaporte.listing_cpi import CartaportesListadoTable

def cartaportes_table_partial(request):
	print (f"\n+++ on cartaportes_table_partial")
	qs = Cartaporte.objects.order_by("-fecha_creacion")  # or your preferred ordering
	table = CartaportesListadoTable(qs)
	RequestConfig(request, paginate={"per_page": 25}).configure(table)
	return render(request, "partials/cartaportes_table.html", {"table": table})

