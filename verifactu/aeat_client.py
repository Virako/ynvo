from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

import requests
from cryptography.hazmat.primitives.serialization import (
    BestAvailableEncryption,
    Encoding,
    NoEncryption,
    pkcs12,
)
from lxml import etree

NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
NS_RESP = (
    "https://www2.agenciatributaria.gob.es/static_files/common/internet"
    "/dep/aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd"
)
NS_SF = (
    "https://www2.agenciatributaria.gob.es/static_files/common/internet"
    "/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
)

ENDPOINTS = {
    "production": (
        "https://www1.agenciatributaria.gob.es"
        "/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP"
    ),
    "test": (
        "https://prewww1.aeat.es/wlpl/TIKE-CONT/ws/SistemaFacturacion/VerifactuSOAP"
    ),
}


class SubmissionStatus(StrEnum):
    CORRECT = "Correcto"
    PARTIALLY_CORRECT = "ParcialmenteCorrecto"
    INCORRECT = "Incorrecto"


class RecordStatus(StrEnum):
    CORRECT = "Correcto"
    ACCEPTED_WITH_ERRORS = "AceptadoConErrores"
    INCORRECT = "Incorrecto"


@dataclass
class RecordResponse:
    status: RecordStatus
    invoice_id: str = ""
    error_code: str = ""
    error_description: str = ""
    is_duplicate: bool = False


@dataclass
class SubmissionResponse:
    status: SubmissionStatus
    csv: str = ""
    wait_time: int = 60
    records: list[RecordResponse] = field(default_factory=list)


@dataclass
class SOAPFault:
    fault_code: str
    fault_string: str


class AEATClientError(Exception):
    pass


class SOAPFaultError(AEATClientError):
    def __init__(self, fault: SOAPFault) -> None:
        self.fault = fault
        super().__init__(f"SOAPFault [{fault.fault_code}]: {fault.fault_string}")


def wrap_in_soap_envelope(xml_bytes: bytes) -> bytes:
    """Wrap VeriFactu XML inside a SOAP 1.1 envelope."""
    inner = etree.fromstring(xml_bytes)
    envelope = etree.Element(
        f"{{{NS_SOAP}}}Envelope",
        nsmap={"soapenv": NS_SOAP},
    )
    etree.SubElement(envelope, f"{{{NS_SOAP}}}Header")
    body = etree.SubElement(envelope, f"{{{NS_SOAP}}}Body")
    body.append(inner)
    return etree.tostring(envelope, xml_declaration=True, encoding="UTF-8")


def parse_response(xml_bytes: bytes) -> SubmissionResponse:
    """Parse AEAT SOAP response XML into a SubmissionResponse."""
    root = etree.fromstring(xml_bytes)

    # Check for SOAPFault
    fault = root.find(f".//{{{NS_SOAP}}}Fault")
    if fault is not None:
        code = fault.findtext("faultcode", default="")
        string = fault.findtext("faultstring", default="")
        raise SOAPFaultError(SOAPFault(fault_code=code, fault_string=string))

    resp = root.find(f".//{{{NS_RESP}}}RespuestaRegFactuSistemaFacturacion")
    if resp is None:
        raise AEATClientError("Missing RespuestaRegFactuSistemaFacturacion")

    csv = resp.findtext(f"{{{NS_RESP}}}CSV", default="")
    wait_time_text = resp.findtext(f"{{{NS_RESP}}}TiempoEsperaEnvio", default="60")
    status_text = resp.findtext(f"{{{NS_RESP}}}EstadoEnvio", default="")

    records: list[RecordResponse] = []
    for line in resp.findall(f"{{{NS_RESP}}}RespuestaLinea"):
        record_status = line.findtext(f"{{{NS_RESP}}}EstadoRegistro", default="")

        id_factura = line.find(f"{{{NS_RESP}}}IDFactura")
        invoice_id = ""
        if id_factura is not None:
            nif = id_factura.findtext(f"{{{NS_SF}}}IDEmisorFactura", default="")
            num = id_factura.findtext(f"{{{NS_SF}}}NumSerieFactura", default="")
            fecha = id_factura.findtext(
                f"{{{NS_SF}}}FechaExpedicionFactura", default=""
            )
            invoice_id = f"{nif}|{num}|{fecha}"

        records.append(
            RecordResponse(
                status=RecordStatus(record_status),
                invoice_id=invoice_id,
                error_code=line.findtext(
                    f"{{{NS_RESP}}}CodigoErrorRegistro", default=""
                ),
                error_description=line.findtext(
                    f"{{{NS_RESP}}}DescripcionErrorRegistro", default=""
                ),
                is_duplicate=line.find(f"{{{NS_RESP}}}RegistroDuplicado") is not None,
            )
        )

    return SubmissionResponse(
        status=SubmissionStatus(status_text),
        csv=csv,
        wait_time=int(wait_time_text),
        records=records,
    )


def pfx_to_pem(pfx_path: str, password: str) -> tuple[str, str]:
    """Convert PFX/P12 certificate to temporary PEM files (cert, key).

    Returns a tuple of (cert_path, key_path). Caller is responsible
    for cleanup — use via CertificateContext.
    """
    pfx_data = Path(pfx_path).read_bytes()
    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        pfx_data, password.encode("UTF-8") if password else None
    )
    if private_key is None or certificate is None:
        raise AEATClientError("PFX file does not contain key and certificate")

    cert_file = tempfile.NamedTemporaryFile(suffix=".pem", delete=False)
    cert_file.write(certificate.public_bytes(Encoding.PEM))
    cert_file.close()

    key_file = tempfile.NamedTemporaryFile(suffix=".pem", delete=False)
    key_file.write(
        private_key.private_bytes(
            Encoding.PEM,
            format=BestAvailableEncryption(password.encode("UTF-8"))
            if password
            else NoEncryption(),
        )  # type: ignore[arg-type]
    )
    key_file.close()

    return cert_file.name, key_file.name


class AEATClient:
    """Client for submitting VeriFactu records to AEAT via SOAP."""

    def __init__(
        self,
        cert_path: str,
        cert_key_path: str,
        environment: str = "test",
        session: requests.Session | None = None,
    ) -> None:
        if environment not in ENDPOINTS:
            raise ValueError(f"Unknown environment: {environment}")
        self.endpoint = ENDPOINTS[environment]
        self.session = session or requests.Session()
        self.session.cert = (cert_path, cert_key_path)
        self.session.headers.update(
            {
                "Content-Type": "text/xml; charset=UTF-8",
                "SOAPAction": "",
            }
        )

    def submit(self, xml_bytes: bytes) -> SubmissionResponse:
        """Submit VeriFactu XML to AEAT. Returns parsed response."""
        soap_xml = wrap_in_soap_envelope(xml_bytes)
        try:
            response = self.session.post(
                self.endpoint,
                data=soap_xml,
                timeout=30,
            )
            response.raise_for_status()
        except requests.ConnectionError as e:
            raise AEATClientError(f"Connection error: {e}") from e
        except requests.Timeout as e:
            raise AEATClientError(f"Request timed out: {e}") from e
        except requests.HTTPError as e:
            # AEAT returns 500 for SOAPFault, try to parse the body
            if e.response is not None and e.response.status_code == 500:
                return parse_response(e.response.content)
            raise AEATClientError(f"HTTP error: {e}") from e

        return parse_response(response.content)
