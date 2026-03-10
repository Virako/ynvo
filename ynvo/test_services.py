from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from verifactu.aeat_client import (
    AEATClientError,
    RecordResponse,
    RecordStatus,
    SubmissionResponse,
    SubmissionStatus,
)

from ynvo.services import (
    _apply_response,
    _format_amount,
    cancel_invoice_record,
    register_invoice,
    submit_to_aeat,
)


# --- Helpers ---


def _make_invoice(
    *,
    vat="B12345678",
    year=2027,
    number=1,
    tax=21,
    proforma=False,
    invoice_record=None,
):
    invoice = MagicMock()
    invoice.invo_from.vat = vat
    invoice.proforma = proforma
    invoice.invoice_record = invoice_record
    invoice.created = date(year, 1, 15)
    invoice.tax = tax
    invoice.number_wadobo.return_value = f"{year}/{number:03d}"
    invoice.get_totals.return_value = [
        ["subtotal", "Subtotal", 1000.0],
        ["tax", f"IVA ({tax}%)", 210.0],
        ["total", "TOTAL", 1210.0],
    ]
    return invoice


def _make_record(**overrides):
    defaults = dict(
        issuer_nif="B12345678",
        serial_number="2027/001",
        issue_date=date(2027, 1, 15),
        invoice_type="F1",
        operation_type="alta",
        total_amount=Decimal("1210.00"),
        tax_amount=Decimal("210.00"),
        tax_breakdown=[
            {"tax_base": "1000.00", "tax_rate": "21", "tax_amount": "210.00"}
        ],
        fingerprint="a" * 64,
        previous_fingerprint="",
        generation_timestamp=MagicMock(),
        xml_content="",
        is_amendment=False,
        prior_rejection="",
        no_prior_record=False,
        status="pending",
        csv_code="",
        aeat_error_code="",
        aeat_error_description="",
        submitted_at=None,
    )
    defaults.update(overrides)
    record = MagicMock(**defaults)
    record.generation_timestamp.strftime.return_value = "2027-01-15T10:00:00+01:00"
    return record


# --- _format_amount ---


def test_format_amount_float():
    assert _format_amount(1000.0) == "1000.00"


def test_format_amount_decimal():
    assert _format_amount(Decimal("1210.50")) == "1210.50"


def test_format_amount_integer():
    assert _format_amount(0) == "0.00"


# --- register_invoice ---


@patch("ynvo.services.build_verification_url", return_value="https://example.com/qr")
@patch("ynvo.services.compute_registration_fingerprint", return_value="f" * 64)
@patch("ynvo.services._build_previous", return_value=None)
@patch("ynvo.services._generation_timestamp")
@patch("ynvo.services.InvoiceRecord")
def test_register_invoice_creates_record(
    mock_ir_cls, mock_ts, mock_prev, mock_fp, mock_qr
):
    mock_ts.return_value = ("2027-01-15T10:00:00+01:00", MagicMock())
    created_record = MagicMock()
    mock_ir_cls.objects.create.return_value = created_record

    invoice = _make_invoice()
    result = register_invoice(invoice)

    assert result is created_record
    mock_ir_cls.objects.create.assert_called_once()
    invoice.save.assert_called_once_with(update_fields=["invoice_record"])
    assert invoice.invoice_record is created_record


@patch("ynvo.services.InvoiceRecord")
def test_register_invoice_raises_if_already_registered(mock_ir_cls):
    invoice = _make_invoice(invoice_record=MagicMock())

    with pytest.raises(ValueError, match="already has a VeriFactu record"):
        register_invoice(invoice)


@patch("ynvo.services.InvoiceRecord")
def test_register_invoice_raises_if_proforma(mock_ir_cls):
    invoice = _make_invoice(proforma=True)

    with pytest.raises(ValueError, match="Cannot register a proforma"):
        register_invoice(invoice)


@patch("ynvo.services.build_verification_url", return_value="https://example.com/qr")
@patch("ynvo.services.compute_registration_fingerprint", return_value="f" * 64)
@patch("ynvo.services._build_previous")
@patch("ynvo.services._generation_timestamp")
@patch("ynvo.services.InvoiceRecord")
def test_register_invoice_uses_previous_fingerprint(
    mock_ir_cls, mock_ts, mock_prev, mock_fp, mock_qr
):
    prev = MagicMock(fingerprint="b" * 64)
    mock_prev.return_value = prev
    mock_ts.return_value = ("2027-01-15T10:00:00+01:00", MagicMock())
    mock_ir_cls.objects.create.return_value = MagicMock()

    invoice = _make_invoice()
    register_invoice(invoice)

    call_kwargs = mock_ir_cls.objects.create.call_args.kwargs
    assert call_kwargs["previous_fingerprint"] == "b" * 64


# --- cancel_invoice_record ---


@patch("ynvo.services.compute_cancellation_fingerprint", return_value="c" * 64)
@patch("ynvo.services._build_previous", return_value=None)
@patch("ynvo.services._generation_timestamp")
@patch("ynvo.services.InvoiceRecord")
def test_cancel_invoice_record_creates_cancellation(
    mock_ir_cls, mock_ts, mock_prev, mock_fp
):
    mock_ts.return_value = ("2027-01-15T10:00:00+01:00", MagicMock())
    original = _make_record()
    cancel_record = MagicMock()
    mock_ir_cls.objects.create.return_value = cancel_record

    invoice = MagicMock()
    invoice.invoice_record = original

    result = cancel_invoice_record(invoice)

    assert result is cancel_record
    call_kwargs = mock_ir_cls.objects.create.call_args.kwargs
    assert call_kwargs["operation_type"] == "anulacion"
    assert call_kwargs["serial_number"] == original.serial_number


def test_cancel_invoice_record_raises_without_record():
    invoice = MagicMock()
    invoice.invoice_record = None

    with pytest.raises(ValueError, match="no VeriFactu record to cancel"):
        cancel_invoice_record(invoice)


# --- _apply_response ---


def test_apply_response_correct():
    record = _make_record()
    response = SubmissionResponse(
        status=SubmissionStatus.CORRECT, csv="1234567890123456", records=[]
    )

    _apply_response(record, response)

    assert record.status == "accepted"
    assert record.csv_code == "1234567890123456"
    record.save.assert_called_once()


def test_apply_response_record_accepted_with_errors():
    record = _make_record()
    response = SubmissionResponse(
        status=SubmissionStatus.PARTIALLY_CORRECT,
        csv="1234567890123456",
        records=[
            RecordResponse(
                status=RecordStatus.ACCEPTED_WITH_ERRORS,
                error_code="1234",
                error_description="Minor issue",
            )
        ],
    )

    _apply_response(record, response)

    assert record.status == "accepted_errors"
    assert record.aeat_error_code == "1234"
    assert record.aeat_error_description == "Minor issue"


def test_apply_response_record_rejected():
    record = _make_record()
    response = SubmissionResponse(
        status=SubmissionStatus.INCORRECT,
        csv="",
        records=[
            RecordResponse(
                status=RecordStatus.INCORRECT,
                error_code="4100",
                error_description="Invalid NIF",
            )
        ],
    )

    _apply_response(record, response)

    assert record.status == "rejected"
    assert record.aeat_error_code == "4100"


def test_apply_response_no_records_means_rejected():
    record = _make_record()
    response = SubmissionResponse(
        status=SubmissionStatus.INCORRECT, csv="", records=[]
    )

    _apply_response(record, response)

    assert record.status == "rejected"


# --- submit_to_aeat ---


@patch("ynvo.services._apply_response")
@patch("ynvo.services.AEATClient")
@patch("ynvo.services._build_registration_xml", return_value=b"<xml/>")
def test_submit_to_aeat_registration(mock_build, mock_client_cls, mock_apply):
    record = _make_record(operation_type="alta")
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_response = MagicMock()
    mock_client.submit.return_value = mock_response

    submit_to_aeat(record)

    mock_build.assert_called_once_with(record)
    mock_client.submit.assert_called_once_with(b"<xml/>")
    mock_apply.assert_called_once_with(record, mock_response)
    assert record.xml_content == "<xml/>"


@patch("ynvo.services._apply_response")
@patch("ynvo.services.AEATClient")
@patch("ynvo.services._build_cancellation_xml", return_value=b"<cancel/>")
def test_submit_to_aeat_cancellation(mock_build, mock_client_cls, mock_apply):
    record = _make_record(operation_type="anulacion")
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_response = MagicMock()
    mock_client.submit.return_value = mock_response

    submit_to_aeat(record)

    mock_build.assert_called_once_with(record)
    mock_client.submit.assert_called_once_with(b"<cancel/>")


@patch("ynvo.services.AEATClient")
@patch("ynvo.services._build_registration_xml", return_value=b"<xml/>")
def test_submit_to_aeat_error_sets_rejected(mock_build, mock_client_cls):
    record = _make_record(operation_type="alta")
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    mock_client.submit.side_effect = AEATClientError("Connection failed")

    with pytest.raises(AEATClientError):
        submit_to_aeat(record)

    assert record.status == "rejected"
    assert record.aeat_error_description == "Connection failed"
    record.save.assert_called_once()
