import os

from django.conf import settings
from django.views.generic.base import TemplateView
from django_weasyprint import WeasyTemplateResponseMixin
from wkhtmltopdf.views import PDFTemplateView

from .models import Invoice


class YnvoView(WeasyTemplateResponseMixin, TemplateView):
    template_name = 'ynvo/ynvo.html'
    filename = 'test.pdf'

    def get_context_data(self, **kwargs):
        self.pk = kwargs.get('pk', None)
        context = super().get_context_data(**kwargs)
        context['ynvo'] = Invoice.objects.filter(number=self.pk).order_by('year').last()
        return context
