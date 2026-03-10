import hashlib

from verifactu.hash import compute_fingerprint

SAMPLE_KWARGS = {
    "issuer_nif": "B12345678",
    "serial_number": "FAC-2027-001",
    "issue_date": "01-01-2027",
    "invoice_type": "F1",
    "tax_amount": "210.00",
    "total_amount": "1210.00",
    "previous_fingerprint": "",
    "generation_timestamp": "2027-01-01T10:00:00+01:00",
}


def _expected_hash(**overrides: str) -> str:
    kwargs = {**SAMPLE_KWARGS, **overrides}
    payload = (
        f"{kwargs['issuer_nif']}{kwargs['serial_number']}{kwargs['issue_date']}"
        f"{kwargs['invoice_type']}{kwargs['tax_amount']}{kwargs['total_amount']}"
        f"{kwargs['previous_fingerprint']}{kwargs['generation_timestamp']}"
    )
    return hashlib.sha256(payload.encode("UTF-8")).hexdigest()


def test_first_invoice_without_previous_fingerprint():
    result = compute_fingerprint(**SAMPLE_KWARGS)
    assert result == _expected_hash()
    assert len(result) == 64


def test_chained_invoice_with_previous_fingerprint():
    first = compute_fingerprint(**SAMPLE_KWARGS)
    chained_kwargs = {
        **SAMPLE_KWARGS,
        "serial_number": "FAC-2027-002",
        "previous_fingerprint": first,
    }
    second = compute_fingerprint(**chained_kwargs)
    assert second == _expected_hash(**chained_kwargs)
    assert second != first


def test_changing_any_field_changes_hash():
    base = compute_fingerprint(**SAMPLE_KWARGS)
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
        altered = compute_fingerprint(**{**SAMPLE_KWARGS, field: alt_value})
        assert altered != base, f"Hash should change when '{field}' changes"


def test_deterministic():
    a = compute_fingerprint(**SAMPLE_KWARGS)
    b = compute_fingerprint(**SAMPLE_KWARGS)
    assert a == b
