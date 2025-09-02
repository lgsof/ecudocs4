# from django import forms
# from .models import Usuario
# from django.contrib.auth.forms import UserCreationForm

# class RegistrationForm (UserCreationForm):
#	  email = forms.EmailField (required=True)
#	  class Meta:
#		  model = Usuario
#		  fields = ['username', 'email', 'perfil', 'password1', 'password2']

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import password_validation
from .models import Usuario
from .models import Empresa

#----------------------------------------------------------
#----------------------------------------------------------
from django.contrib.auth.forms import AuthenticationForm

class CustomAuthenticationForm(AuthenticationForm):
	COUNTRY_CHOICES = [('', 'Seleccion el país'), ('ECUADOR','ECUADOR'),('COLOMBIA','COLOMBIA'),('PERU','PERU'),('TODOS','TODOS')]
	pais = forms.ChoiceField (choices=COUNTRY_CHOICES, required=True)

	username = forms.CharField(
		widget=forms.TextInput(attrs={'autofocus': True, 'autocomplete': 'off'})
	)
	password = forms.CharField(
		label=("Password"),
		strip=False,
		widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
	)

#----------------------------------------------------------
#----------------------------------------------------------
class RegistrationForm (UserCreationForm):
	email = forms.EmailField (required=False, widget=forms.EmailInput (attrs={'class': 'form-control'}))
	password1 = forms.CharField (
		label="Ingrese la Clave",
		widget=forms.PasswordInput (attrs={'class': 'form-control', 'id': 'password-input', 'autocomplete':'off'}),
		help_text=password_validation.password_validators_help_text_html (),
	)
	password2 = forms.CharField (
		label="Confirme la Clave",
		widget=forms.PasswordInput (attrs={'class': 'form-control', 'autocomplete':'off'}),
	)

	# Add an additional field for password strength
	password_strength = forms.CharField (
		widget=forms.HiddenInput (),
		required=False,
	)

	username = forms.CharField (
		label="Nombre Usuario",
		widget=forms.TextInput (attrs={'autocomplete':'off'}),
	)

	class Meta:
		model = Usuario
		fields =  ('username', 'email', 'nombre', 'pais', 'perfil', 'nro_docs_asignados')

	def __init__ (self, *args, **kwargs):
		super().__init__ (*args, **kwargs)
		self.fields ["username"].label = "Usuario"
		self.fields ["email"].label    = "Correo"
		self.fields ["nombre"].label   = "Nombre completo (Nombre + Apellido)"
		self.fields ["pais"].label	   = "Pais"
		self.fields ["perfil"].label   = "Tipo de usuario"


class EmpresaCreateForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ["nickname", "nombre", "activo"]
        widgets = {
            "codigo": forms.TextInput(attrs={"placeholder": "subdominio, p.ej. byza"}),
            "nombre": forms.TextInput(attrs={"placeholder": "Nombre visible, p.ej. BYZA S.A."}),
        }
