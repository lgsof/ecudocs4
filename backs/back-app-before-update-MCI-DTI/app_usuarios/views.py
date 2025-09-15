from django.shortcuts import render, redirect
from .forms import RegistrationForm
from django.contrib import messages

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

from django.contrib.auth.views import PasswordChangeView

from .models import Usuario
from .tables import UserTable
from .forms  import CustomAuthenticationForm

#----------------------------------------------------------
# Custom login view added "pais"
#----------------------------------------------------------
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm
#from .forms import CountrySelectionForm

#----------------------------------------------------------
# Handling login
#----------------------------------------------------------
class CustomLoginView (LoginView):
	template_name = 'login.html'  # Update with your login template path
	authentication_form = CustomAuthenticationForm

	def get_context_data(self, **kwargs):
		context = super().get_context_data (**kwargs)
		return context

	def post (self, request, *args, **kwargs):
		print (f"\n\n\n+++ DEBUG: CustomLoginView POST '{request}'")
		auth_form    = self.authentication_form (data=request.POST)

		if auth_form.is_valid(): 
			# Process login and country selection
			request.session ['usuario'] = auth_form.cleaned_data ['username']
			request.session ['pais'] = auth_form.cleaned_data ['pais']
			request.session.save ()
			usuario = request.session ['usuario'] 
			pais    = request.session ['pais'] 
			print (f"+++ DEBUG: CustomLoginView self.request.session '{usuario}'")
			print (f"+++ DEBUG: CustomLoginView self.request.session '{pais}'")
			return self.form_valid (auth_form)
		else:
			return self.form_invalid (auth_form)

	def form_invalid(self, form):
		context = self.get_context_data (form=form)
		return self.render_to_response(context)
	
#----------------------------------------------------------
# Get username when called from html login template
#----------------------------------------------------------
from django.http import JsonResponse
from django.contrib.auth import get_user_model

User = get_user_model()

def get_country_for_username (request):
	username = request.POST.get ('username', None)
	data = {'pais': ''}
	print ("+++ DEBUG: get_country_for_username : username :", username)
	if username:
		try:
			user = User.objects.get (username=username)
			print ("+++ DEBUG: get_country_for_username : user.pais :", user.pais)
			data['pais'] = user.pais
		except User.DoesNotExist:
			data['pais'] = ''

	request.session ['pais']  = data ['pais']
	request.session.save ()
	return JsonResponse(data)

#----------------------------------------------------------
#----------------------------------------------------------
class UserCreate (LoginRequiredMixin, CreateView):
	model = Usuario
	fields = ['username','email', 'nombre', 'pais', 'password', 'perfil', 
	          'nro_docs_creados', 'nro_docs_asignados']
	template_name = 'user_create.html'
	success_url = reverse_lazy ('listar')

class UserDelete (LoginRequiredMixin, DeleteView):
	model = Usuario
	template_name = 'user_delete.html'
	success_url = reverse_lazy ('listar')

class UserUpdate (LoginRequiredMixin, UpdateView):
	model = Usuario
	fields = ['username','email', 'nombre', 'pais', 'perfil', 
	          'nro_docs_creados', 'nro_docs_asignados']
	template_name = 'user_update.html'
	success_url = reverse_lazy ('listar')

	def get_form(self, form_class=None):
		form = super().get_form (form_class)
		form.fields['username'].widget.attrs['readonly'] = True  # Set username field as readonly
		return form	

def user_list(request):
	print ("--- user_list ---")
	if (not request.user.is_staff):
		url =  reverse_lazy ("index")
		return redirect (url)

	users = Usuario.objects.all()
	table = UserTable (users)
	return render(request, 'user_list.html', {'table': table})	

def registration (request):
	if request.method == 'POST':
		# Create a form that has request.POST
		form = RegistrationForm(request.POST)
		if form.is_valid():
			user = form.save (commit=False)
			print (user)
			# Set the user's password securely
			username  = form.cleaned_data['username']		 
			password1 = form.cleaned_data['password1']
			password2 = form.cleaned_data['password2']

			# Set user type flag
			perfil              = form.cleaned_data['perfil']		 
			user.es_director    = perfil == "director"
			user.es_funcionario = perfil == "funcionario"
			user.es_externo     = perfil == "externo"

			user.is_staff       = user.es_director

			if password1 == password2:
				user.set_password (password1)
				user.save()
				
				messages.success(request, f'Su cuenta ha sido creada {username} ! Proceda a ingresar')
				return redirect('listar')  # Redirect to the login page
			else:
				# Handle password mismatch error here
				form.add_error('password2', 'Claves ingresadas no coinciden')

	else:
		form = RegistrationForm()
	return render(request, 'registration.html', {'form': form})

#----------------------------------------------------------
# Password change view
#----------------------------------------------------------
class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
	template_name = 'password_change_form.html'
	success_url   = reverse_lazy('login')
	success_message = "Cambio exitoso. Por favor ingrese con su nueva clave"

