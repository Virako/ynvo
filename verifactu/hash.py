import hashlib


def compute_registration_fingerprint(
    *,
    issuer_nif: str,
    serial_number: str,
    issue_date: str,
    invoice_type: str,
    tax_amount: str,
    total_amount: str,
    previous_fingerprint: str,
    generation_timestamp: str,
) -> str:
    """Compute SHA-256 fingerprint for registration records.

    Format per Orden HAC/1177/2024:
        IDEmisorFactura=...&NumSerieFactura=...&...

    Values are NOT URL-encoded.
    """
    payload = "&".join([
        f"IDEmisorFactura={issuer_nif}",
        f"NumSerieFactura={serial_number}",
        f"FechaExpedicionFactura={issue_date}",
        f"TipoFactura={invoice_type}",
        f"CuotaTotal={tax_amount}",
        f"ImporteTotal={total_amount}",
        f"Huella={previous_fingerprint}",
        f"FechaHoraHusoGenRegistro={generation_timestamp}",
    ])
    return hashlib.sha256(payload.encode("UTF-8")).hexdigest().upper()


def compute_cancellation_fingerprint(
    *,
    issuer_nif: str,
    serial_number: str,
    issue_date: str,
    previous_fingerprint: str,
    generation_timestamp: str,
) -> str:
    """Compute SHA-256 fingerprint for cancellation records.

    Format per Orden HAC/1177/2024:
        IDEmisorFacturaAnulada=...&NumSerieFacturaAnulada=...&...

    Values are NOT URL-encoded.
    """
    payload = "&".join([
        f"IDEmisorFacturaAnulada={issuer_nif}",
        f"NumSerieFacturaAnulada={serial_number}",
        f"FechaExpedicionFacturaAnulada={issue_date}",
        f"Huella={previous_fingerprint}",
        f"FechaHoraHusoGenRegistro={generation_timestamp}",
    ])
    return hashlib.sha256(payload.encode("UTF-8")).hexdigest().upper()
