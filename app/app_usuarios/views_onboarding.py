# app_usuarios/views_onboarding.py
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import EmpresaCreateForm

@staff_member_required
def crear_empresa(request):
    if request.method == "POST":
        form = EmpresaCreateForm(request.POST)
        if form.is_valid():
            empresa = form.save()
            # Tras crear, puedes mostrar instrucciones para entrar por subdominio
            return redirect(reverse("onboarding_exito") + f"?nickname={empresa.nickname}")
    else:
        form = EmpresaCreateForm()
    return render(request, "onboarding/crear_empresa.html", {"form": form})

@staff_member_required
def onboarding_exito(request):
    nickname = request.GET.get("nickname", "")
    # Puedes componer URL de acceso (prod y dev)
    contexto = {
        "nickname": nickname,
        "url_prod": f"https://{nickname}.ecuapassdocs.app",
        "url_dev":  f"http://{nickname}.localhost:8000",
    }
    return render(request, "onboarding/exito.html", contexto)

