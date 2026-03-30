from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from django_verifactu.models import InvoiceRecord


@admin.register(InvoiceRecord)
class InvoiceRecordAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = (
        "serial_number",
        "issuer_nif",
        "issue_date",
        "invoice_type",
        "operation_type",
        "status",
        "xml_download",
    )
    list_filter = ("status", "operation_type", "invoice_type")
    search_fields = ("serial_number", "issuer_nif")
    readonly_fields = (
        "issuer_nif",
        "serial_number",
        "issue_date",
        "invoice_type",
        "operation_type",
        "total_amount",
        "tax_amount",
        "tax_breakdown",
        "fingerprint",
        "previous_fingerprint",
        "generation_timestamp",
        "is_amendment",
        "prior_rejection",
        "no_prior_record",
        "status",
        "csv_code",
        "aeat_response",
        "aeat_error_code",
        "aeat_error_description",
        "submitted_at",
        "qr_url",
        "xml_download",
    )
    exclude = ("xml_content",)

    def xml_download(self, obj):
        if not obj.xml_content:
            return "-"
        url = reverse("django_verifactu:download_xml", args=[obj.pk])
        return format_html("<a href='{}'>XML</a>", url)

    xml_download.short_description = "XML"  # type: ignore[attr-defined]

    def has_add_permission(self, request):  # type: ignore[override]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[override]
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).for_user(request.user)
