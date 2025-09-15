from django.shortcuts import render
from django.views import View

class InfoView(View):
	template_name = 'info_reportes.html'

	def get(self, request, *args, **kwargs):
		return render(request, self.template_name)
