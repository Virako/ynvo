from __future__ import annotations

from django.db import models


class InvoiceRecordQuerySet(models.QuerySet):  # type: ignore[type-arg]
    def pending(self) -> InvoiceRecordQuerySet:
        return self.filter(status="pending")

    def by_issuer(self, nif: str) -> InvoiceRecordQuerySet:
        return self.filter(issuer_nif=nif)

    def chain_ordered(self) -> InvoiceRecordQuerySet:
        return self.order_by("id")


class InvoiceRecordManager(models.Manager):  # type: ignore[type-arg]
    def get_queryset(self) -> InvoiceRecordQuerySet:
        return InvoiceRecordQuerySet(self.model, using=self._db)

    def last_fingerprint(self, issuer_nif: str) -> str:
        record = (
            self.get_queryset()
            .by_issuer(issuer_nif)
            .chain_ordered()
            .last()
        )
        return record.fingerprint if record else ""
