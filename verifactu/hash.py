import hashlib


def compute_fingerprint(
    issuer_nif: str,
    serial_number: str,
    issue_date: str,
    invoice_type: str,
    tax_amount: str,
    total_amount: str,
    previous_fingerprint: str,
    generation_timestamp: str,
) -> str:
    """Compute SHA-256 fingerprint per Orden HAC/1177/2024.

    Concatenation order:
        IDEmisorFactura + NumSerieFactura + FechaExpedicionFactura +
        TipoFactura + CuotaTotal + ImporteTotal +
        Huella_RegistroAnterior + FechaHoraHusoGenRegistro
    """
    payload = (
        f"{issuer_nif}{serial_number}{issue_date}"
        f"{invoice_type}{tax_amount}{total_amount}"
        f"{previous_fingerprint}{generation_timestamp}"
    )
    return hashlib.sha256(payload.encode("UTF-8")).hexdigest()
