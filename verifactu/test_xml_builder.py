from lxml import etree

from verifactu.constants import InvoiceType
from verifactu.xml_builder import (
    CancellationData,
    CorrectionAmount,
    InvoiceData,
    PreviousInvoice,
    RectifiedInvoice,
    SoftwareInfo,
    TaxDetail,
    build_cancellation_xml,
    build_registration_xml,
    validate_xml,
)

SOFTWARE = SoftwareInfo(
    name="Test Company",
    nif="B12345678",
    software_name="ynvo",
    version="1.0",
)


def _sample_invoice(**overrides):  # type: ignore[no-untyped-def]
    defaults = {
        "issuer_nif": "B12345678",
        "issuer_name": "Test Company",
        "serial_number": "FAC-2027-001",
        "issue_date": "01-01-2027",
        "invoice_type": InvoiceType.F1,
        "description": "Servicios de desarrollo",
        "recipient_name": "Client Corp",
        "recipient_nif": "A87654321",
        "tax_details": [
            TaxDetail(
                tax_base="1000.00",
                tax_rate="21.00",
                tax_amount="210.00",
            )
        ],
        "tax_amount": "210.00",
        "total_amount": "1210.00",
        "fingerprint": "a" * 64,
        "generation_timestamp": "2027-01-01T10:00:00+01:00",
        "software": SOFTWARE,
    }
    defaults.update(overrides)
    return InvoiceData(**defaults)  # type: ignore[arg-type]


def test_registration_xml_is_valid_xml():
    xml = build_registration_xml(_sample_invoice())
    doc = etree.fromstring(xml)
    assert doc.tag.endswith("RegFactuSistemaFacturacion")


def test_registration_xml_contains_required_fields():
    data = _sample_invoice()
    xml = build_registration_xml(data)
    text = xml.decode("UTF-8")
    assert "B12345678" in text
    assert "FAC-2027-001" in text
    assert "01-01-2027" in text
    assert "1210.00" in text
    assert "210.00" in text
    assert "Test Company" in text
    assert "Client Corp" in text
    assert "a" * 64 in text


def test_registration_xml_first_in_chain():
    xml = build_registration_xml(_sample_invoice())
    text = xml.decode("UTF-8")
    assert "PrimerRegistro" in text
    assert "RegistroAnterior" not in text


def test_registration_xml_chained():
    previous = PreviousInvoice(
        issuer_nif="B12345678",
        serial_number="FAC-2026-100",
        issue_date="31-12-2026",
        fingerprint="b" * 64,
    )
    xml = build_registration_xml(_sample_invoice(previous=previous))
    text = xml.decode("UTF-8")
    assert "RegistroAnterior" in text
    assert "PrimerRegistro" not in text
    assert "FAC-2026-100" in text
    assert "b" * 64 in text


def test_registration_xml_multiple_tax_details():
    details = [
        TaxDetail(
            tax_base="800.00",
            tax_rate="21.00",
            tax_amount="168.00",
        ),
        TaxDetail(
            tax_base="200.00",
            tax_rate="10.00",
            tax_amount="20.00",
        ),
    ]
    xml = build_registration_xml(
        _sample_invoice(tax_details=details)
    )
    text = xml.decode("UTF-8")
    assert text.count("DetalleDesglose") == 4  # 2 open + 2 close


PREVIOUS = PreviousInvoice(
    issuer_nif="B12345678",
    serial_number="FAC-2027-000",
    issue_date="31-12-2026",
    fingerprint="b" * 64,
)


def test_cancellation_xml_is_valid_xml():
    data = CancellationData(
        issuer_nif="B12345678",
        issuer_name="Test Company",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
        fingerprint="c" * 64,
        generation_timestamp="2027-01-02T10:00:00+01:00",
        software=SOFTWARE,
        previous=PREVIOUS,
    )
    xml = build_cancellation_xml(data)
    doc = etree.fromstring(xml)
    assert doc.tag.endswith("RegFactuSistemaFacturacion")


def test_cancellation_xml_contains_anulacion_fields():
    data = CancellationData(
        issuer_nif="B12345678",
        issuer_name="Test Company",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
        fingerprint="c" * 64,
        generation_timestamp="2027-01-02T10:00:00+01:00",
        software=SOFTWARE,
        previous=PREVIOUS,
    )
    xml = build_cancellation_xml(data)
    text = xml.decode("UTF-8")
    assert "RegistroAnulacion" in text
    assert "IDEmisorFacturaAnulada" in text
    assert "NumSerieFacturaAnulada" in text
    assert "FechaExpedicionFacturaAnulada" in text


def test_validate_xml_against_xsd():
    xml = build_registration_xml(_sample_invoice())
    errors = validate_xml(xml)
    assert errors == [], f"XSD validation errors: {errors}"


def test_invoice_with_irpf_valid_against_xsd():
    """Factura con IRPF: la retención se refleja en ImporteTotal."""
    xml = build_registration_xml(
        _sample_invoice(
            tax_amount="210.00",
            total_amount="1060.00",  # 1000 + 210 IVA - 150 IRPF
        )
    )
    errors = validate_xml(xml)
    assert errors == [], f"XSD validation errors: {errors}"
    text = xml.decode("UTF-8")
    assert "1060.00" in text


def test_rectificativa_incremental():
    """Factura rectificativa por diferencia (incremental)."""
    rectified = RectifiedInvoice(
        issuer_nif="B12345678",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
    )
    xml = build_registration_xml(
        _sample_invoice(
            serial_number="FAC-2027-002",
            invoice_type=InvoiceType.R1,
            correction_type="I",
            rectified_invoices=[rectified],
            tax_amount="-21.00",
            total_amount="-121.00",
        )
    )
    text = xml.decode("UTF-8")
    assert "TipoRectificativa" in text
    assert ">I<" in text
    assert "FacturasRectificadas" in text
    assert "IDFacturaRectificada" in text
    assert "FAC-2027-001" in text
    assert "ImporteRectificacion" not in text


def test_rectificativa_incremental_valid_against_xsd():
    """Factura rectificativa incremental válida contra XSD."""
    rectified = RectifiedInvoice(
        issuer_nif="B12345678",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
    )
    xml = build_registration_xml(
        _sample_invoice(
            serial_number="FAC-2027-002",
            invoice_type=InvoiceType.R1,
            correction_type="I",
            rectified_invoices=[rectified],
            tax_amount="-21.00",
            total_amount="-121.00",
        )
    )
    errors = validate_xml(xml)
    assert errors == [], f"XSD validation errors: {errors}"


def test_rectificativa_sustitutiva():
    """Factura rectificativa por sustitución con ImporteRectificacion."""
    rectified = RectifiedInvoice(
        issuer_nif="B12345678",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
    )
    correction = CorrectionAmount(base="1000.00", tax="210.00")
    xml = build_registration_xml(
        _sample_invoice(
            serial_number="FAC-2027-003",
            invoice_type=InvoiceType.R1,
            correction_type="S",
            rectified_invoices=[rectified],
            correction_amount=correction,
            tax_details=[
                TaxDetail(
                    tax_base="800.00",
                    tax_rate="21.00",
                    tax_amount="168.00",
                )
            ],
            tax_amount="168.00",
            total_amount="968.00",
        )
    )
    text = xml.decode("UTF-8")
    assert ">S<" in text
    assert "ImporteRectificacion" in text
    assert "BaseRectificada" in text
    assert "CuotaRectificada" in text


def test_rectificativa_sustitutiva_valid_against_xsd():
    """Factura rectificativa sustitutiva válida contra XSD."""
    rectified = RectifiedInvoice(
        issuer_nif="B12345678",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
    )
    correction = CorrectionAmount(base="1000.00", tax="210.00")
    xml = build_registration_xml(
        _sample_invoice(
            serial_number="FAC-2027-003",
            invoice_type=InvoiceType.R1,
            correction_type="S",
            rectified_invoices=[rectified],
            correction_amount=correction,
            tax_details=[
                TaxDetail(
                    tax_base="800.00",
                    tax_rate="21.00",
                    tax_amount="168.00",
                )
            ],
            tax_amount="168.00",
            total_amount="968.00",
        )
    )
    errors = validate_xml(xml)
    assert errors == [], f"XSD validation errors: {errors}"


# --- Phase 3b: amendment, prior rejection, no prior record ---


def test_amendment_registration():
    """Alta de subsanación: corrige RF aceptado/con errores."""
    xml = build_registration_xml(
        _sample_invoice(is_amendment=True)
    )
    text = xml.decode("UTF-8")
    assert ">S<" in text
    assert "Subsanacion" in text


def test_amendment_registration_valid_against_xsd():
    xml = build_registration_xml(
        _sample_invoice(is_amendment=True)
    )
    errors = validate_xml(xml)
    assert errors == [], f"XSD validation errors: {errors}"


def test_prior_rejection_registration():
    """Alta por rechazo: is_amendment=True + prior_rejection='X'."""
    xml = build_registration_xml(
        _sample_invoice(is_amendment=True, prior_rejection="X")
    )
    text = xml.decode("UTF-8")
    assert "Subsanacion" in text
    assert "RechazoPrevio" in text
    assert ">X<" in text


def test_prior_rejection_registration_valid_against_xsd():
    xml = build_registration_xml(
        _sample_invoice(is_amendment=True, prior_rejection="X")
    )
    errors = validate_xml(xml)
    assert errors == [], f"XSD validation errors: {errors}"


def test_normal_registration_omits_amendment_fields():
    """Alta normal no incluye Subsanacion ni RechazoPrevio."""
    xml = build_registration_xml(_sample_invoice())
    text = xml.decode("UTF-8")
    assert "Subsanacion" not in text
    assert "RechazoPrevio" not in text


def test_cancellation_prior_rejection():
    """Anulación por rechazo: prior_rejection=True."""
    data = CancellationData(
        issuer_nif="B12345678",
        issuer_name="Test Company",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
        fingerprint="c" * 64,
        generation_timestamp="2027-01-02T10:00:00+01:00",
        software=SOFTWARE,
        previous=PREVIOUS,
        prior_rejection=True,
    )
    xml = build_cancellation_xml(data)
    text = xml.decode("UTF-8")
    assert "RechazoPrevio" in text
    assert "SinRegistroPrevio" not in text


def test_cancellation_prior_rejection_valid_against_xsd():
    data = CancellationData(
        issuer_nif="B12345678",
        issuer_name="Test Company",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
        fingerprint="c" * 64,
        generation_timestamp="2027-01-02T10:00:00+01:00",
        software=SOFTWARE,
        previous=PREVIOUS,
        prior_rejection=True,
    )
    errors = validate_xml(build_cancellation_xml(data))
    assert errors == [], f"XSD validation errors: {errors}"


def test_cancellation_no_prior_record():
    """Anulación sin registro previo: no_prior_record=True."""
    data = CancellationData(
        issuer_nif="B12345678",
        issuer_name="Test Company",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
        fingerprint="c" * 64,
        generation_timestamp="2027-01-02T10:00:00+01:00",
        software=SOFTWARE,
        previous=PREVIOUS,
        no_prior_record=True,
    )
    xml = build_cancellation_xml(data)
    text = xml.decode("UTF-8")
    assert "SinRegistroPrevio" in text
    assert "RechazoPrevio" not in text


def test_cancellation_no_prior_record_valid_against_xsd():
    data = CancellationData(
        issuer_nif="B12345678",
        issuer_name="Test Company",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
        fingerprint="c" * 64,
        generation_timestamp="2027-01-02T10:00:00+01:00",
        software=SOFTWARE,
        previous=PREVIOUS,
        no_prior_record=True,
    )
    errors = validate_xml(build_cancellation_xml(data))
    assert errors == [], f"XSD validation errors: {errors}"


def test_normal_cancellation_omits_extra_fields():
    """Anulación normal no incluye SinRegistroPrevio ni RechazoPrevio."""
    data = CancellationData(
        issuer_nif="B12345678",
        issuer_name="Test Company",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
        fingerprint="c" * 64,
        generation_timestamp="2027-01-02T10:00:00+01:00",
        software=SOFTWARE,
        previous=PREVIOUS,
    )
    text = build_cancellation_xml(data).decode("UTF-8")
    assert "SinRegistroPrevio" not in text
    assert "RechazoPrevio" not in text


def test_validate_xml_returns_errors_for_invalid_xml():
    invalid_xml = b'<?xml version="1.0"?><Invalid/>'
    errors = validate_xml(invalid_xml)
    assert len(errors) > 0
