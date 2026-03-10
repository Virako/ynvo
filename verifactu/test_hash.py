import hashlib

from verifactu.hash import (
    compute_cancellation_fingerprint,
    compute_registration_fingerprint,
)

REGISTRATION_KWARGS = {
    "issuer_nif": "B12345678",
    "serial_number": "FAC-2027-001",
    "issue_date": "01-01-2027",
    "invoice_type": "F1",
    "tax_amount": "210.00",
    "total_amount": "1210.00",
    "previous_fingerprint": "",
    "generation_timestamp": "2027-01-01T10:00:00+01:00",
}


def _expected_registration_hash(**overrides: str) -> str:
    kw = {**REGISTRATION_KWARGS, **overrides}
    payload = "&".join([
        f"IDEmisorFactura={kw['issuer_nif']}",
        f"NumSerieFactura={kw['serial_number']}",
        f"FechaExpedicionFactura={kw['issue_date']}",
        f"TipoFactura={kw['invoice_type']}",
        f"CuotaTotal={kw['tax_amount']}",
        f"ImporteTotal={kw['total_amount']}",
        f"Huella={kw['previous_fingerprint']}",
        f"FechaHoraHusoGenRegistro={kw['generation_timestamp']}",
    ])
    return hashlib.sha256(payload.encode("UTF-8")).hexdigest().upper()


# Registration fingerprint tests


def test_first_invoice_without_previous_fingerprint():
    result = compute_registration_fingerprint(**REGISTRATION_KWARGS)
    assert result == _expected_registration_hash()
    assert len(result) == 64


def test_result_is_uppercase():
    result = compute_registration_fingerprint(**REGISTRATION_KWARGS)
    assert result == result.upper()


def test_chained_invoice_with_previous_fingerprint():
    first = compute_registration_fingerprint(**REGISTRATION_KWARGS)
    chained_kwargs = {
        **REGISTRATION_KWARGS,
        "serial_number": "FAC-2027-002",
        "previous_fingerprint": first,
    }
    second = compute_registration_fingerprint(**chained_kwargs)
    assert second == _expected_registration_hash(**chained_kwargs)
    assert second != first


def test_changing_any_field_changes_hash():
    base = compute_registration_fingerprint(**REGISTRATION_KWARGS)
    for field, alt_value in [
        ("issuer_nif", "A99999999"),
        ("serial_number", "FAC-2027-999"),
        ("issue_date", "31-12-2027"),
        ("invoice_type", "F2"),
        ("tax_amount", "0.00"),
        ("total_amount", "999.99"),
        ("previous_fingerprint", "abc123"),
        ("generation_timestamp", "2027-12-31T23:59:59+01:00"),
    ]:
        altered = compute_registration_fingerprint(
            **{**REGISTRATION_KWARGS, field: alt_value}
        )
        assert altered != base, f"Hash should change when '{field}' changes"


def test_deterministic():
    a = compute_registration_fingerprint(**REGISTRATION_KWARGS)
    b = compute_registration_fingerprint(**REGISTRATION_KWARGS)
    assert a == b


# Cancellation fingerprint tests


CANCELLATION_KWARGS = {
    "issuer_nif": "B12345678",
    "serial_number": "FAC-2027-001",
    "issue_date": "01-01-2027",
    "previous_fingerprint": "A" * 64,
    "generation_timestamp": "2027-01-02T10:00:00+01:00",
}


def test_cancellation_fingerprint():
    result = compute_cancellation_fingerprint(**CANCELLATION_KWARGS)
    assert len(result) == 64
    assert result == result.upper()


def test_cancellation_uses_anulada_field_names():
    """Cancellation hash uses different field names than registration."""
    reg_result = compute_registration_fingerprint(
        **REGISTRATION_KWARGS,
    )
    cancel_result = compute_cancellation_fingerprint(
        **CANCELLATION_KWARGS,
    )
    assert reg_result != cancel_result


# Vectores oficiales AEAT (Orden HAC/1177/2024)


def test_aeat_first_record_vector():
    """Caso 1 AEAT: primer registro sin huella previa."""
    result = compute_registration_fingerprint(
        issuer_nif="89890001K",
        serial_number="12345678/G33",
        issue_date="01-01-2024",
        invoice_type="F1",
        tax_amount="12.35",
        total_amount="123.45",
        previous_fingerprint="",
        generation_timestamp="2024-01-01T19:20:30+01:00",
    )
    assert result == (
        "3C464DAF61ACB827C65FDA19F352A4E3BDC2C640E9E9FC4CC058073F38F12F60"
    )


def test_aeat_chained_record_vector():
    """Caso 2 AEAT: registro encadenado con huella del caso 1."""
    first = compute_registration_fingerprint(
        issuer_nif="89890001K",
        serial_number="12345678/G33",
        issue_date="01-01-2024",
        invoice_type="F1",
        tax_amount="12.35",
        total_amount="123.45",
        previous_fingerprint="",
        generation_timestamp="2024-01-01T19:20:30+01:00",
    )
    result = compute_registration_fingerprint(
        issuer_nif="89890001K",
        serial_number="12345679/G34",
        issue_date="01-01-2024",
        invoice_type="F1",
        tax_amount="12.35",
        total_amount="123.45",
        previous_fingerprint=first,
        generation_timestamp="2024-01-01T19:20:35+01:00",
    )
    assert result == (
        "F7B94CFD8924EDFF273501B01EE5153E4CE8F259766F88CF6ACB8935802A2B97"
    )


def test_aeat_cancellation_vector():
    """Caso 3 AEAT: anulación encadenada con huella del caso 2."""
    second = compute_registration_fingerprint(
        issuer_nif="89890001K",
        serial_number="12345679/G34",
        issue_date="01-01-2024",
        invoice_type="F1",
        tax_amount="12.35",
        total_amount="123.45",
        previous_fingerprint=(
            "3C464DAF61ACB827C65FDA19F352A4E3"
            "BDC2C640E9E9FC4CC058073F38F12F60"
        ),
        generation_timestamp="2024-01-01T19:20:35+01:00",
    )
    result = compute_cancellation_fingerprint(
        issuer_nif="89890001K",
        serial_number="12345679/G34",
        issue_date="01-01-2024",
        previous_fingerprint=second,
        generation_timestamp="2024-01-01T19:20:40+01:00",
    )
    assert result == (
        "177547C0D57AC74748561D054A9CEC14B4C4EA23D1BEFD6F2E69E3A388F90C68"
    )
