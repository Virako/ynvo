from verifactu.constants import AEAT_PRODUCTION_URL, AEAT_TEST_URL
from verifactu.qr import build_verification_url, generate_qr_image


def test_build_url_test_environment():
    url = build_verification_url(
        nif="B12345678",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
        total_amount="1210.00",
    )
    assert url.startswith(AEAT_TEST_URL)
    assert "nif=B12345678" in url
    assert "numserie=FAC-2027-001" in url
    assert "fecha=01-01-2027" in url
    assert "importe=1210.00" in url


def test_build_url_production_environment():
    url = build_verification_url(
        nif="B12345678",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
        total_amount="1210.00",
        production=True,
    )
    assert url.startswith(AEAT_PRODUCTION_URL)


def test_different_environments_generate_different_urls():
    url_test = build_verification_url(
        nif="B12345678",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
        total_amount="1210.00",
    )
    url_prod = build_verification_url(
        nif="B12345678",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
        total_amount="1210.00",
        production=True,
    )
    assert url_test != url_prod


def test_generate_qr_image_returns_valid_png():
    url = build_verification_url(
        nif="B12345678",
        serial_number="FAC-2027-001",
        issue_date="01-01-2027",
        total_amount="1210.00",
    )
    image_bytes = generate_qr_image(url)
    assert isinstance(image_bytes, bytes)
    assert len(image_bytes) > 0
    # PNG magic bytes
    assert image_bytes[:8] == b"\x89PNG\r\n\x1a\n"
