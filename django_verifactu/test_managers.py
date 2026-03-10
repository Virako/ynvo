import datetime
from decimal import Decimal

import pytest

from django_verifactu.models import InvoiceRecord


@pytest.fixture()
def _sample_records(db):
    defaults = {
        "issue_date": datetime.date(2027, 1, 1),
        "total_amount": Decimal("1210.00"),
        "tax_amount": Decimal("210.00"),
        "generation_timestamp": datetime.datetime(
            2027, 1, 1, 10, 0, tzinfo=datetime.UTC
        ),
    }
    InvoiceRecord.objects.create(
        issuer_nif="B12345678",
        serial_number="FAC-2027-001",
        fingerprint="a" * 64,
        **defaults,
    )
    InvoiceRecord.objects.create(
        issuer_nif="B12345678",
        serial_number="FAC-2027-002",
        fingerprint="b" * 64,
        previous_fingerprint="a" * 64,
        **defaults,
    )
    InvoiceRecord.objects.create(
        issuer_nif="A99999999",
        serial_number="FAC-2027-001",
        fingerprint="c" * 64,
        status="accepted",
        **defaults,
    )


@pytest.mark.usefixtures("_sample_records")
class TestInvoiceRecordManager:
    def test_last_fingerprint(self):
        fp = InvoiceRecord.objects.last_fingerprint("B12345678")
        assert fp == "b" * 64

    def test_last_fingerprint_unknown_issuer(self):
        fp = InvoiceRecord.objects.last_fingerprint("X00000000")
        assert fp == ""

    def test_pending(self):
        qs = InvoiceRecord.objects.get_queryset().pending()
        assert qs.count() == 2

    def test_by_issuer(self):
        qs = InvoiceRecord.objects.get_queryset().by_issuer("B12345678")
        assert qs.count() == 2

    def test_chain_ordered(self):
        qs = (
            InvoiceRecord.objects.get_queryset()
            .by_issuer("B12345678")
            .chain_ordered()
        )
        serials = list(qs.values_list("serial_number", flat=True))
        assert serials == ["FAC-2027-001", "FAC-2027-002"]
