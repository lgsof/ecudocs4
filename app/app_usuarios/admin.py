# app_usuarios/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.conf import settings
from .models import Usuario, Empresa

# --- Usuario ---
class UsuarioAdmin(UserAdmin):
    readonly_fields = ('date_joined',)
    list_display = ('username', 'empresa', 'email', 'perfil', 'is_staff', 'date_joined')
    list_filter  = ('perfil', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('nombre', 'empresa', 'pais', 'email', 'perfil')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('username', 'email', 'password1', 'password2', 'perfil')}),
    )

admin.site.register(Usuario, UsuarioAdmin)

# --- Empresa ---
@admin.action(description="Activar empresas seleccionadas")
def activar_empresas(modeladmin, request, queryset):
    queryset.update(activo=True)

@admin.action(description="Desactivar empresas seleccionadas")
def desactivar_empresas(modeladmin, request, queryset):
    queryset.update(activo=False)

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
	list_display  = ("nickname", "nombre", "permiso", "activo", "fecha_creacion", "link_dev", "link_prod")
	list_filter   = ("activo",)
	search_fields = ("nickname", "nombre")
	actions		  = (activar_empresas, desactivar_empresas)
	prepopulated_fields = {"nickname": ("nombre",)}
	readonly_fields = ("fecha_creacion",)  # auto_now_add -> not editable

	# (no fieldsets -> Django shows all editable fields automatically)

	# Control *order* explicitly (include readonly fields where you want them)
	fields = (
		"nickname",
		"nombre",
		"permiso",
		"activo",
		"nit",
		"direccion",
		"telefono",
		"email",
		"fecha_creacion",	# readonly, but placed here
	)	

	def save_model(self, request, obj, form, change):
		# Normaliza el subdominio
		if obj.nickname:
			obj.nickname = obj.nickname.strip().lower()
		super().save_model(request, obj, form, change)

	def link_dev(self, obj):
		# Link a http://<nickname>.localhost:8000/
		return format_html('<a href="http://{}.localhost:8000/" target="_blank">dev</a>', obj.nickname)
	link_dev.short_description = "Dev"

	def link_prod(self, obj):
		# Usa tu dominio base; configurable por settings.TENANT_BASE_DOMAIN
		base = getattr(settings, "TENANT_BASE_DOMAIN", "ecuapassdocs.app")
		return format_html('<a href="https://{}.{}" target="_blank">prod</a>', obj.nickname, base)
	link_prod.short_description = "Prod"

