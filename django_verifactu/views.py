from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views import View

from django_verifactu.models import InvoiceRecord


class DownloadXMLView(LoginRequiredMixin, View):
    def get(self, request, pk):
        try:
            record = InvoiceRecord.objects.for_user(request.user).get(pk=pk)
        except InvoiceRecord.DoesNotExist:
            return HttpResponse("Not found", status=404)
        if not record.xml_content:
            return HttpResponse("No XML content", status=404)
        filename = f"verifactu-{record.serial_number.replace('/', '-')}.xml"
        response = HttpResponse(record.xml_content, content_type="application/xml")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
