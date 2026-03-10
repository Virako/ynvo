from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests
from lxml import etree

from verifactu.aeat_client import (
    ENDPOINTS,
    NS_RESP,
    NS_SF,
    NS_SOAP,
    AEATClient,
    AEATClientError,
    RecordStatus,
    SOAPFaultError,
    SubmissionStatus,
    parse_response,
    pfx_to_pem,
    wrap_in_soap_envelope,
)


def _build_soap_response(
    status: str = "Correcto",
    csv: str = "ABC1234567890123",
    wait_time: int = 60,
    records: list[dict[str, str]] | None = None,
) -> bytes:
    """Build a fake AEAT SOAP response XML."""
    nsmap = {"soapenv": NS_SOAP, "sfR": NS_RESP, "sf": NS_SF}
    envelope = etree.Element(f"{{{NS_SOAP}}}Envelope", nsmap=nsmap)
    body = etree.SubElement(envelope, f"{{{NS_SOAP}}}Body")
    resp = etree.SubElement(body, f"{{{NS_RESP}}}RespuestaRegFactuSistemaFacturacion")

    csv_el = etree.SubElement(resp, f"{{{NS_RESP}}}CSV")
    csv_el.text = csv

    wait_el = etree.SubElement(resp, f"{{{NS_RESP}}}TiempoEsperaEnvio")
    wait_el.text = str(wait_time)

    status_el = etree.SubElement(resp, f"{{{NS_RESP}}}EstadoEnvio")
    status_el.text = status

    if records:
        for rec in records:
            line = etree.SubElement(resp, f"{{{NS_RESP}}}RespuestaLinea")

            id_fac = etree.SubElement(line, f"{{{NS_RESP}}}IDFactura")
            nif_el = etree.SubElement(id_fac, f"{{{NS_SF}}}IDEmisorFactura")
            nif_el.text = rec.get("nif", "B12345678")
            num_el = etree.SubElement(id_fac, f"{{{NS_SF}}}NumSerieFactura")
            num_el.text = rec.get("serial", "FAC-2027-001")
            fecha_el = etree.SubElement(id_fac, f"{{{NS_SF}}}FechaExpedicionFactura")
            fecha_el.text = rec.get("date", "01-01-2027")

            op = etree.SubElement(line, f"{{{NS_RESP}}}Operacion")
            tipo_op = etree.SubElement(op, f"{{{NS_SF}}}TipoOperacion")
            tipo_op.text = "A0"

            estado = etree.SubElement(line, f"{{{NS_RESP}}}EstadoRegistro")
            estado.text = rec.get("status", "Correcto")

            if "error_code" in rec:
                code_el = etree.SubElement(line, f"{{{NS_RESP}}}CodigoErrorRegistro")
                code_el.text = rec["error_code"]
            if "error_desc" in rec:
                desc_el = etree.SubElement(
                    line, f"{{{NS_RESP}}}DescripcionErrorRegistro"
                )
                desc_el.text = rec["error_desc"]
            if rec.get("duplicate"):
                etree.SubElement(line, f"{{{NS_RESP}}}RegistroDuplicado")

    return etree.tostring(envelope, xml_declaration=True, encoding="UTF-8")


def _build_soap_fault(code: str = "soap:Server", string: str = "Error") -> bytes:
    nsmap = {"soapenv": NS_SOAP}
    envelope = etree.Element(f"{{{NS_SOAP}}}Envelope", nsmap=nsmap)
    body = etree.SubElement(envelope, f"{{{NS_SOAP}}}Body")
    fault = etree.SubElement(body, f"{{{NS_SOAP}}}Fault")
    fc = etree.SubElement(fault, "faultcode")
    fc.text = code
    fs = etree.SubElement(fault, "faultstring")
    fs.text = string
    return etree.tostring(envelope, xml_declaration=True, encoding="UTF-8")


SAMPLE_XML = b"<?xml version='1.0'?><root/>"


@pytest.fixture()
def mock_session() -> MagicMock:
    return MagicMock()


def _make_client(mock_session: MagicMock, environment: str = "test") -> AEATClient:
    return AEATClient(
        cert_path="/tmp/cert.pem",
        cert_key_path="/tmp/key.pem",
        environment=environment,
        session=mock_session,
    )


# --- wrap_in_soap_envelope ---


def test_wrap_produces_valid_soap():
    result = wrap_in_soap_envelope(b"<Foo><Bar>1</Bar></Foo>")
    doc = etree.fromstring(result)
    assert doc.tag == f"{{{NS_SOAP}}}Envelope"
    body = doc.find(f"{{{NS_SOAP}}}Body")
    assert body is not None
    assert body[0].tag == "Foo"


def test_wrap_preserves_inner_xml():
    inner = b"<Test attr='val'>content</Test>"
    result = wrap_in_soap_envelope(inner)
    text = result.decode("UTF-8")
    assert "content" in text
    assert "Test" in text


# --- parse_response ---


def test_parse_correct_response():
    xml = _build_soap_response(
        status="Correcto",
        csv="ABCD123456789012",
        wait_time=90,
        records=[{"status": "Correcto"}],
    )
    resp = parse_response(xml)
    assert resp.status == SubmissionStatus.CORRECT
    assert resp.csv == "ABCD123456789012"
    assert resp.wait_time == 90
    assert len(resp.records) == 1
    assert resp.records[0].status == RecordStatus.CORRECT


def test_parse_partially_correct_response():
    xml = _build_soap_response(
        status="ParcialmenteCorrecto",
        records=[
            {"status": "Correcto", "serial": "FAC-001"},
            {
                "status": "Incorrecto",
                "serial": "FAC-002",
                "error_code": "1234",
                "error_desc": "NIF inválido",
            },
        ],
    )
    resp = parse_response(xml)
    assert resp.status == SubmissionStatus.PARTIALLY_CORRECT
    assert len(resp.records) == 2
    assert resp.records[0].status == RecordStatus.CORRECT
    assert resp.records[1].status == RecordStatus.INCORRECT
    assert resp.records[1].error_code == "1234"
    assert resp.records[1].error_description == "NIF inválido"


def test_parse_incorrect_response():
    xml = _build_soap_response(
        status="Incorrecto",
        csv="",
        records=[
            {
                "status": "Incorrecto",
                "error_code": "5000",
                "error_desc": "Error de formato",
            },
        ],
    )
    resp = parse_response(xml)
    assert resp.status == SubmissionStatus.INCORRECT


def test_parse_accepted_with_errors():
    xml = _build_soap_response(
        status="ParcialmenteCorrecto",
        records=[
            {
                "status": "AceptadoConErrores",
                "error_code": "1001",
                "error_desc": "Campo opcional incorrecto",
            },
        ],
    )
    resp = parse_response(xml)
    assert resp.records[0].status == RecordStatus.ACCEPTED_WITH_ERRORS


def test_parse_duplicate_record():
    xml = _build_soap_response(
        status="Incorrecto",
        records=[{"status": "Incorrecto", "duplicate": "true"}],
    )
    resp = parse_response(xml)
    assert resp.records[0].is_duplicate is True


def test_parse_invoice_id():
    xml = _build_soap_response(
        records=[
            {
                "status": "Correcto",
                "nif": "B99999999",
                "serial": "FAC-2027-042",
                "date": "15-06-2027",
            }
        ],
    )
    resp = parse_response(xml)
    assert resp.records[0].invoice_id == "B99999999|FAC-2027-042|15-06-2027"


def test_parse_soap_fault():
    xml = _build_soap_fault(code="soap:Client", string="XML mal formado")
    with pytest.raises(SOAPFaultError) as exc_info:
        parse_response(xml)
    assert exc_info.value.fault.fault_code == "soap:Client"
    assert "XML mal formado" in str(exc_info.value)


def test_parse_missing_response_element():
    envelope = (
        b"<?xml version='1.0'?>"
        b"<soapenv:Envelope xmlns:soapenv='http://schemas.xmlsoap.org/soap/envelope/'>"
        b"<soapenv:Body><Empty/></soapenv:Body>"
        b"</soapenv:Envelope>"
    )
    with pytest.raises(AEATClientError, match="Missing"):
        parse_response(envelope)


def test_parse_wait_time():
    xml = _build_soap_response(wait_time=120)
    resp = parse_response(xml)
    assert resp.wait_time == 120


# --- AEATClient ---


def test_client_uses_test_endpoint(mock_session: MagicMock):
    client = _make_client(mock_session, "test")
    assert client.endpoint == ENDPOINTS["test"]


def test_client_uses_production_endpoint(mock_session: MagicMock):
    client = _make_client(mock_session, "production")
    assert client.endpoint == ENDPOINTS["production"]


def test_client_rejects_unknown_environment(mock_session: MagicMock):
    with pytest.raises(ValueError, match="Unknown environment"):
        _make_client(mock_session, "staging")


def test_client_sets_cert_on_session(mock_session: MagicMock):
    _make_client(mock_session)
    assert mock_session.cert == ("/tmp/cert.pem", "/tmp/key.pem")


def test_client_submit_success(mock_session: MagicMock):
    response_xml = _build_soap_response(
        status="Correcto",
        csv="TEST123456789012",
        records=[{"status": "Correcto"}],
    )
    mock_response = MagicMock()
    mock_response.content = response_xml
    mock_response.raise_for_status = MagicMock()
    mock_session.post.return_value = mock_response

    client = _make_client(mock_session)
    result = client.submit(SAMPLE_XML)

    assert result.status == SubmissionStatus.CORRECT
    assert result.csv == "TEST123456789012"
    mock_session.post.assert_called_once()


def test_client_submit_connection_error(mock_session: MagicMock):
    mock_session.post.side_effect = requests.ConnectionError("refused")

    client = _make_client(mock_session)
    with pytest.raises(AEATClientError, match="Connection error"):
        client.submit(SAMPLE_XML)


def test_client_submit_timeout(mock_session: MagicMock):
    mock_session.post.side_effect = requests.Timeout("timed out")

    client = _make_client(mock_session)
    with pytest.raises(AEATClientError, match="timed out"):
        client.submit(SAMPLE_XML)


def test_client_submit_soap_fault_on_500(mock_session: MagicMock):
    fault_xml = _build_soap_fault("soap:Server", "Internal error")
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.content = fault_xml
    mock_response.raise_for_status.side_effect = requests.HTTPError(
        response=mock_response
    )
    mock_session.post.return_value = mock_response

    client = _make_client(mock_session)
    with pytest.raises(SOAPFaultError):
        client.submit(SAMPLE_XML)


def test_client_submit_http_error_non_500(mock_session: MagicMock):
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.raise_for_status.side_effect = requests.HTTPError(
        response=mock_response
    )
    mock_session.post.return_value = mock_response

    client = _make_client(mock_session)
    with pytest.raises(AEATClientError, match="HTTP error"):
        client.submit(SAMPLE_XML)


def test_pfx_to_pem_raises_on_invalid_pfx(tmp_path):
    bad_pfx = tmp_path / "bad.pfx"
    bad_pfx.write_bytes(b"not a pfx file")
    with pytest.raises(Exception):
        pfx_to_pem(str(bad_pfx), "password")
