import os

from django.views.generic.base import TemplateView
from django.shortcuts import get_object_or_404

from .models import Invoice


class YnvoView(TemplateView):
    template_name = "ynvo/ynvo.html"

    def get_context_data(self, year: int = 0, number: str = "", **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        self.ynvo = get_object_or_404(
            Invoice, year=year, number=number, invo_from__user=user
        )
        context["ynvo"] = self.ynvo
        return context

    def get_pdf_filename(self):
        return f"{self.ynvo.invo_to.alias}-{self.ynvo.number}.pdf"
