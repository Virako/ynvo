from django_verifactu.models import InvoiceRecord


def test_is_first_in_chain_when_no_previous():
    record = InvoiceRecord(previous_fingerprint="")
    assert record.is_first_in_chain is True


def test_is_not_first_in_chain_when_previous():
    record = InvoiceRecord(previous_fingerprint="a" * 64)
    assert record.is_first_in_chain is False


def test_is_editable_when_pending():
    record = InvoiceRecord(status="pending")
    assert record.is_editable is True


def test_is_not_editable_when_accepted():
    record = InvoiceRecord(status="accepted")
    assert record.is_editable is False


def test_str():
    record = InvoiceRecord(serial_number="FAC-2027-001", status="pending")
    assert "FAC-2027-001" in str(record)
