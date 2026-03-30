from django.db import models

from django_verifactu.managers import InvoiceRecordManager
from verifactu.constants import InvoiceType


class InvoiceRecord(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("accepted_errors", "Accepted with errors"),
        ("rejected", "Rejected"),
    ]
    OPERATION_CHOICES = [
        ("alta", "Alta"),
        ("anulacion", "Anulación"),
    ]

    issuer_nif = models.CharField(max_length=32)
    serial_number = models.CharField(max_length=64)
    issue_date = models.DateField()
    invoice_type = models.CharField(
        max_length=2,
        choices=[(t.value, t.name) for t in InvoiceType],
        default=InvoiceType.F1,
    )
    operation_type = models.CharField(
        max_length=10, choices=OPERATION_CHOICES, default="alta"
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_breakdown = models.JSONField(default=list)
    fingerprint = models.CharField(max_length=64)
    previous_fingerprint = models.CharField(max_length=64, blank=True, default="")
    generation_timestamp = models.DateTimeField()
    xml_content = models.TextField(blank=True, default="")

    # Amendment / rejection fields
    is_amendment = models.BooleanField(default=False)
    prior_rejection = models.CharField(max_length=1, blank=True, default="")
    no_prior_record = models.BooleanField(default=False)

    # AEAT response
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        help_text=(
            "Pending: registered locally (hash + QR generated), not sent to AEAT.<br>"
            "In No VeriFactu mode this is the normal permanent state.<br>"
            "Other statuses only apply after automatic submission via submit_to_aeat()."
        ),
    )
    csv_code = models.CharField(max_length=16, blank=True, default="")
    aeat_response = models.TextField(blank=True, default="")
    aeat_error_code = models.CharField(max_length=5, blank=True, default="")
    aeat_error_description = models.TextField(blank=True, default="")
    submitted_at = models.DateTimeField(null=True, blank=True)
    qr_url = models.URLField(blank=True, default="")

    objects = InvoiceRecordManager()

    class Meta:
        ordering = ("id",)
        indexes = [
            models.Index(fields=["issuer_nif", "serial_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.serial_number} ({self.get_status_display()})"

    @property
    def is_first_in_chain(self) -> bool:
        return self.previous_fingerprint == ""

    @property
    def is_editable(self) -> bool:
        return self.status == "pending"
