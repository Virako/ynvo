from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.conf import settings
from django.utils import timezone

from django_verifactu.models import InvoiceRecord
from verifactu.aeat_client import (
    AEATClient,
    AEATClientError,
    RecordStatus,
    SubmissionResponse,
    SubmissionStatus,
)
from verifactu.constants import InvoiceType
from verifactu.hash import (
    compute_cancellation_fingerprint,
    compute_registration_fingerprint,
)
from verifactu.qr import build_verification_url
from verifactu.xml_builder import (
    CancellationData,
    InvoiceData,
    PreviousInvoice,
    SoftwareInfo,
    TaxDetail,
    build_cancellation_xml,
    build_registration_xml,
)

if TYPE_CHECKING:
    from ynvo.models import Invoice


# --- Helpers ---


def _get_software_info() -> SoftwareInfo:
    return SoftwareInfo(
        name=getattr(settings, "VERIFACTU_SOFTWARE_COMPANY", ""),
        nif=getattr(settings, "VERIFACTU_SOFTWARE_NIF", ""),
        software_name=getattr(settings, "VERIFACTU_SOFTWARE_NAME", "ynvo"),
        version=getattr(settings, "VERIFACTU_SOFTWARE_VERSION", "1.0"),
    )


def _format_amount(value: float | Decimal) -> str:
    return f"{Decimal(str(value)):.2f}"


def _issue_date_str(invoice: Invoice) -> str:
    return invoice.created.strftime("%d-%m-%Y")


def _build_previous(issuer_nif: str) -> PreviousInvoice | None:
    record = (
        InvoiceRecord.objects.get_queryset()
        .by_issuer(issuer_nif)
        .chain_ordered()
        .last()
    )
    if record is None:
        return None
    return PreviousInvoice(
        issuer_nif=record.issuer_nif,
        serial_number=record.serial_number,
        issue_date=record.issue_date.strftime("%d-%m-%Y"),
        fingerprint=record.fingerprint,
    )


def _generation_timestamp() -> tuple[str, timezone.datetime]:
    now = timezone.now()
    return now.strftime("%Y-%m-%dT%H:%M:%S+01:00"), now


# --- Registration ---


def register_invoice(invoice: Invoice) -> InvoiceRecord:
    """Create a VeriFactu record for an invoice."""
    if invoice.invoice_record is not None:
        raise ValueError("Invoice already has a VeriFactu record")
    if invoice.proforma:
        raise ValueError("Cannot register a proforma invoice")

    issuer_nif = invoice.invo_from.vat
    serial_number = invoice.number_wadobo()
    issue_date = _issue_date_str(invoice)
    totals = invoice.get_totals()

    subtotal = next(t[2] for t in totals if t[0] == "subtotal")
    tax_row = next((t for t in totals if t[0] == "tax"), None)
    tax_amount = tax_row[2] if tax_row else 0.0
    total_row = next(t for t in totals if t[0] == "total")
    total_amount = total_row[2]

    timestamp_str, now = _generation_timestamp()
    previous = _build_previous(issuer_nif)
    previous_fingerprint = previous.fingerprint if previous else ""

    fingerprint = compute_registration_fingerprint(
        issuer_nif=issuer_nif,
        serial_number=serial_number,
        issue_date=issue_date,
        invoice_type=InvoiceType.F1,
        tax_amount=_format_amount(tax_amount),
        total_amount=_format_amount(total_amount),
        previous_fingerprint=previous_fingerprint,
        generation_timestamp=timestamp_str,
    )

    environment = getattr(settings, "VERIFACTU_ENVIRONMENT", "test")
    qr_url = build_verification_url(
        nif=issuer_nif,
        serial_number=serial_number,
        issue_date=issue_date,
        total_amount=_format_amount(total_amount),
        production=(environment == "production"),
    )

    record = InvoiceRecord.objects.create(
        issuer_nif=issuer_nif,
        serial_number=serial_number,
        issue_date=invoice.created,
        invoice_type=InvoiceType.F1,
        operation_type="alta",
        total_amount=Decimal(str(round(total_amount, 2))),
        tax_amount=Decimal(str(round(tax_amount, 2))),
        tax_breakdown=[
            {
                "tax_base": _format_amount(subtotal),
                "tax_rate": str(invoice.tax),
                "tax_amount": _format_amount(tax_amount),
            }
        ],
        fingerprint=fingerprint,
        previous_fingerprint=previous_fingerprint,
        generation_timestamp=now,
        qr_url=qr_url,
    )

    record.xml_content = _build_registration_xml(record).decode("UTF-8")
    record.save(update_fields=["xml_content"])

    invoice.invoice_record = record
    invoice.save(update_fields=["invoice_record"])
    return record


# --- Cancellation ---


def cancel_invoice_record(invoice: Invoice) -> InvoiceRecord:
    """Create a cancellation record for an invoice."""
    if invoice.invoice_record is None:
        raise ValueError("Invoice has no VeriFactu record to cancel")

    original = invoice.invoice_record
    issuer_nif = original.issuer_nif
    timestamp_str, now = _generation_timestamp()

    previous = _build_previous(issuer_nif)
    previous_fingerprint = previous.fingerprint if previous else ""

    fingerprint = compute_cancellation_fingerprint(
        issuer_nif=issuer_nif,
        serial_number=original.serial_number,
        issue_date=original.issue_date.strftime("%d-%m-%Y"),
        previous_fingerprint=previous_fingerprint,
        generation_timestamp=timestamp_str,
    )

    return InvoiceRecord.objects.create(
        issuer_nif=issuer_nif,
        serial_number=original.serial_number,
        issue_date=original.issue_date,
        invoice_type=original.invoice_type,
        operation_type="anulacion",
        total_amount=original.total_amount,
        tax_amount=original.tax_amount,
        tax_breakdown=original.tax_breakdown,
        fingerprint=fingerprint,
        previous_fingerprint=previous_fingerprint,
        generation_timestamp=now,
    )


# --- AEAT submission ---


def _build_registration_xml(record: InvoiceRecord) -> bytes:
    software = _get_software_info()
    previous = _build_previous(record.issuer_nif)
    breakdown = record.tax_breakdown or []
    tax_details = [
        TaxDetail(
            tax_base=td["tax_base"],
            tax_rate=td["tax_rate"],
            tax_amount=td["tax_amount"],
        )
        for td in breakdown
    ]
    data = InvoiceData(
        issuer_nif=record.issuer_nif,
        issuer_name=software.name,
        serial_number=record.serial_number,
        issue_date=record.issue_date.strftime("%d-%m-%Y"),
        invoice_type=InvoiceType(record.invoice_type),
        description="Servicios profesionales",
        recipient_name="",
        recipient_nif="",
        tax_details=tax_details,
        tax_amount=_format_amount(record.tax_amount),
        total_amount=_format_amount(record.total_amount),
        fingerprint=record.fingerprint,
        generation_timestamp=record.generation_timestamp.strftime(
            "%Y-%m-%dT%H:%M:%S+01:00"
        ),
        software=software,
        previous=previous,
        is_amendment=record.is_amendment,
        prior_rejection=record.prior_rejection,
    )
    return build_registration_xml(data)


def _build_cancellation_xml(record: InvoiceRecord) -> bytes:
    software = _get_software_info()
    previous = _build_previous(record.issuer_nif)
    if previous is None:
        raise ValueError("Cancellation requires a previous record")
    data = CancellationData(
        issuer_nif=record.issuer_nif,
        issuer_name=software.name,
        serial_number=record.serial_number,
        issue_date=record.issue_date.strftime("%d-%m-%Y"),
        fingerprint=record.fingerprint,
        generation_timestamp=record.generation_timestamp.strftime(
            "%Y-%m-%dT%H:%M:%S+01:00"
        ),
        software=software,
        previous=previous,
        no_prior_record=record.no_prior_record,
        prior_rejection=record.prior_rejection,
    )
    return build_cancellation_xml(data)


def _apply_response(record: InvoiceRecord, response: SubmissionResponse) -> None:
    record.csv_code = response.csv
    record.submitted_at = timezone.now()

    if response.status == SubmissionStatus.CORRECT:
        record.status = "accepted"
    elif response.records:
        r = response.records[0]
        if r.status == RecordStatus.CORRECT:
            record.status = "accepted"
        elif r.status == RecordStatus.ACCEPTED_WITH_ERRORS:
            record.status = "accepted_errors"
            record.aeat_error_code = r.error_code
            record.aeat_error_description = r.error_description
        else:
            record.status = "rejected"
            record.aeat_error_code = r.error_code
            record.aeat_error_description = r.error_description
    else:
        record.status = "rejected"

    record.save()


def submit_to_aeat(record: InvoiceRecord) -> None:
    """Submit an InvoiceRecord to AEAT via SOAP."""
    if record.operation_type == "alta":
        xml = _build_registration_xml(record)
    else:
        xml = _build_cancellation_xml(record)

    record.xml_content = xml.decode("UTF-8")

    client = AEATClient(
        cert_path=getattr(settings, "VERIFACTU_CERT_PATH", ""),
        cert_key_path=getattr(settings, "VERIFACTU_CERT_KEY_PATH", ""),
        environment=getattr(settings, "VERIFACTU_ENVIRONMENT", "test"),
    )
    try:
        response = client.submit(xml)
    except AEATClientError as e:
        record.status = "rejected"
        record.aeat_error_description = str(e)
        record.save()
        raise

    _apply_response(record, response)
