from django.views.generic import TemplateView
from django.utils import timezone
from datetime import date

class Index(TemplateView):
    template_name = 'notebook/index.html'