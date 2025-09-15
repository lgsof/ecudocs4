from django.contrib import admin

# Register your models here.
from app_cartaporte.models_doccpi import Cartaporte
from app_manifiesto.models_docmci import Manifiesto, ManifiestoForm
from app_declaracion.models_docdti import Declaracion, DeclaracionForm
from app_entidades.models_Entidades import Cliente, Conductor, Vehiculo

#admin.site.register(Cliente)
#admin.site.register(Conductor)
admin.site.register(Vehiculo)
#admin.site.register(Cartaporte)
#admin.site.register(Manifiesto)

# Define the admin class
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'id', 'direccion', 'ciudad', 'pais')

# Register the admin class with the associated model
admin.site.register(Cliente, ClienteAdmin)

class ConductorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'documento', 'pais', 'licencia')

# Register the admin class with the associated model
admin.site.register(Conductor, ConductorAdmin)

class ManifiestosInline(admin.TabularInline):
    model = Manifiesto

class CartaporteAdmin(admin.ModelAdmin):
    list_display = ('numero', 'remitente', 'fecha_emision')
    inlines = [ManifiestosInline]

admin.site.register(Cartaporte, CartaporteAdmin)

class ManifiestoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'vehiculo', 'cartaporte', 'fecha_emision')

admin.site.register(Manifiesto, ManifiestoAdmin)

class DeclaracionAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cartaporte', 'fecha_emision')

admin.site.register(Declaracion, DeclaracionAdmin)

