from io import BytesIO
from urllib.parse import urlencode

import qrcode  # type: ignore[import-untyped]

from verifactu.constants import AEAT_PRODUCTION_URL, AEAT_TEST_URL


def build_verification_url(
    *,
    nif: str,
    serial_number: str,
    issue_date: str,
    total_amount: str,
    production: bool = False,
) -> str:
    """Genera la URL de verificación de la AEAT para el código QR."""
    base_url = AEAT_PRODUCTION_URL if production else AEAT_TEST_URL
    params = urlencode({
        "nif": nif,
        "numserie": serial_number,
        "fecha": issue_date,
        "importe": total_amount,
    })
    return f"{base_url}?{params}"


def generate_qr_image(url: str) -> bytes:
    """Genera una imagen PNG del código QR a partir de una URL."""
    img = qrcode.make(url)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
