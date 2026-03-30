from django.urls import path

from django_verifactu.views import DownloadXMLView

app_name = "django_verifactu"

urlpatterns = [
    path(
        "invoicerecord/<int:pk>/xml/",
        DownloadXMLView.as_view(),
        name="download_xml",
    ),
]
