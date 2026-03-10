from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from verifactu.constants import InvoiceType

NS_SF = (
    "https://www2.agenciatributaria.gob.es/static_files/common/internet"
    "/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
)
NS_SLR = (
    "https://www2.agenciatributaria.gob.es/static_files/common/internet"
    "/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd"
)
NSMAP = {"sf": NS_SF, "sfLR": NS_SLR}
SCHEMAS_DIR = Path(__file__).parent / "schemas"


@dataclass
class TaxDetail:
    tax_base: str
    tax_rate: str
    tax_amount: str
    tax_type: str = "01"  # 01=IVA
    operation_type: str = "S1"  # S1=sujeta no exenta sin inversión


@dataclass
class SoftwareInfo:
    name: str
    nif: str
    software_name: str
    software_id: str = "01"
    version: str = "1.0"
    installation_number: str = "01"
    verifactu_only: str = "S"
    multi_ot: str = "N"
    multiple_ot: str = "N"


@dataclass
class PreviousInvoice:
    issuer_nif: str
    serial_number: str
    issue_date: str
    fingerprint: str


@dataclass
class RectifiedInvoice:
    issuer_nif: str
    serial_number: str
    issue_date: str


@dataclass
class CorrectionAmount:
    base: str
    tax: str


@dataclass
class InvoiceData:
    issuer_nif: str
    issuer_name: str
    serial_number: str
    issue_date: str
    invoice_type: InvoiceType
    description: str
    recipient_name: str
    recipient_nif: str
    tax_details: list[TaxDetail]
    tax_amount: str
    total_amount: str
    fingerprint: str
    generation_timestamp: str
    software: SoftwareInfo
    previous: PreviousInvoice | None = None
    regime_key: str = "01"
    correction_type: str | None = None  # "S"=sustitutiva, "I"=incremental
    rectified_invoices: list[RectifiedInvoice] | None = None
    correction_amount: CorrectionAmount | None = None
    is_amendment: bool = False  # Subsanacion=S
    prior_rejection: str = ""  # RechazoPrevio: "S", "X", or ""


@dataclass
class CancellationData:
    issuer_nif: str
    issuer_name: str
    serial_number: str
    issue_date: str
    fingerprint: str
    generation_timestamp: str
    software: SoftwareInfo
    previous: PreviousInvoice  # always required for cancellation
    no_prior_record: bool = False  # SinRegistroPrevio=S
    prior_rejection: bool = False  # RechazoPrevio=S


def _sf(tag: str) -> str:
    return f"{{{NS_SF}}}{tag}"


def _slr(tag: str) -> str:
    return f"{{{NS_SLR}}}{tag}"


def _add_sub(parent: etree._Element, tag: str, text: str) -> etree._Element:
    el = etree.SubElement(parent, tag)
    el.text = text
    return el


def _build_header(
    root: etree._Element, issuer_nif: str, issuer_name: str
) -> None:
    cabecera = etree.SubElement(root, _slr("Cabecera"))
    obligado = etree.SubElement(cabecera, _sf("ObligadoEmision"))
    _add_sub(obligado, _sf("NombreRazon"), issuer_name)
    _add_sub(obligado, _sf("NIF"), issuer_nif)


def _build_software(
    parent: etree._Element, sw: SoftwareInfo
) -> None:
    sistema = etree.SubElement(parent, _sf("SistemaInformatico"))
    _add_sub(sistema, _sf("NombreRazon"), sw.name)
    _add_sub(sistema, _sf("NIF"), sw.nif)
    _add_sub(sistema, _sf("NombreSistemaInformatico"), sw.software_name)
    _add_sub(sistema, _sf("IdSistemaInformatico"), sw.software_id)
    _add_sub(sistema, _sf("Version"), sw.version)
    _add_sub(sistema, _sf("NumeroInstalacion"), sw.installation_number)
    _add_sub(
        sistema, _sf("TipoUsoPosibleSoloVerifactu"), sw.verifactu_only
    )
    _add_sub(sistema, _sf("TipoUsoPosibleMultiOT"), sw.multi_ot)
    _add_sub(sistema, _sf("IndicadorMultiplesOT"), sw.multiple_ot)


def _build_chaining(
    parent: etree._Element, previous: PreviousInvoice | None
) -> None:
    enc = etree.SubElement(parent, _sf("Encadenamiento"))
    if previous is None:
        _add_sub(enc, _sf("PrimerRegistro"), "S")
    else:
        reg = etree.SubElement(enc, _sf("RegistroAnterior"))
        _add_sub(reg, _sf("IDEmisorFactura"), previous.issuer_nif)
        _add_sub(reg, _sf("NumSerieFactura"), previous.serial_number)
        _add_sub(
            reg, _sf("FechaExpedicionFactura"), previous.issue_date
        )
        _add_sub(reg, _sf("Huella"), previous.fingerprint)


def build_registration_xml(data: InvoiceData) -> bytes:
    """Genera XML de alta de factura según XSD de AEAT."""
    root = etree.Element(
        _slr("RegFactuSistemaFacturacion"), nsmap=NSMAP
    )

    _build_header(root, data.issuer_nif, data.issuer_name)

    reg_factura = etree.SubElement(
        root, _slr("RegistroFactura")
    )
    alta = etree.SubElement(reg_factura, _sf("RegistroAlta"))

    _add_sub(alta, _sf("IDVersion"), "1.0")

    # IDFactura
    id_factura = etree.SubElement(alta, _sf("IDFactura"))
    _add_sub(id_factura, _sf("IDEmisorFactura"), data.issuer_nif)
    _add_sub(id_factura, _sf("NumSerieFactura"), data.serial_number)
    _add_sub(
        id_factura, _sf("FechaExpedicionFactura"), data.issue_date
    )

    _add_sub(alta, _sf("NombreRazonEmisor"), data.issuer_name)

    if data.is_amendment:
        _add_sub(alta, _sf("Subsanacion"), "S")
    if data.prior_rejection:
        _add_sub(alta, _sf("RechazoPrevio"), data.prior_rejection)

    _add_sub(alta, _sf("TipoFactura"), data.invoice_type)

    if data.correction_type is not None:
        _add_sub(alta, _sf("TipoRectificativa"), data.correction_type)

    if data.rectified_invoices:
        facturas_rect = etree.SubElement(
            alta, _sf("FacturasRectificadas")
        )
        for ri in data.rectified_invoices:
            id_rect = etree.SubElement(
                facturas_rect, _sf("IDFacturaRectificada")
            )
            _add_sub(id_rect, _sf("IDEmisorFactura"), ri.issuer_nif)
            _add_sub(id_rect, _sf("NumSerieFactura"), ri.serial_number)
            _add_sub(
                id_rect,
                _sf("FechaExpedicionFactura"),
                ri.issue_date,
            )

    if data.correction_amount is not None:
        importe_rect = etree.SubElement(
            alta, _sf("ImporteRectificacion")
        )
        _add_sub(
            importe_rect,
            _sf("BaseRectificada"),
            data.correction_amount.base,
        )
        _add_sub(
            importe_rect,
            _sf("CuotaRectificada"),
            data.correction_amount.tax,
        )

    _add_sub(alta, _sf("DescripcionOperacion"), data.description)

    # Destinatarios
    destinatarios = etree.SubElement(alta, _sf("Destinatarios"))
    dest = etree.SubElement(destinatarios, _sf("IDDestinatario"))
    _add_sub(dest, _sf("NombreRazon"), data.recipient_name)
    _add_sub(dest, _sf("NIF"), data.recipient_nif)

    # Desglose
    desglose = etree.SubElement(alta, _sf("Desglose"))
    for td in data.tax_details:
        detalle = etree.SubElement(desglose, _sf("DetalleDesglose"))
        _add_sub(detalle, _sf("Impuesto"), td.tax_type)
        _add_sub(detalle, _sf("ClaveRegimen"), data.regime_key)
        _add_sub(detalle, _sf("CalificacionOperacion"), td.operation_type)
        _add_sub(detalle, _sf("TipoImpositivo"), td.tax_rate)
        _add_sub(
            detalle, _sf("BaseImponibleOimporteNoSujeto"), td.tax_base
        )
        _add_sub(detalle, _sf("CuotaRepercutida"), td.tax_amount)

    _add_sub(alta, _sf("CuotaTotal"), data.tax_amount)
    _add_sub(alta, _sf("ImporteTotal"), data.total_amount)

    _build_chaining(alta, data.previous)
    _build_software(alta, data.software)

    _add_sub(
        alta, _sf("FechaHoraHusoGenRegistro"), data.generation_timestamp
    )
    _add_sub(alta, _sf("TipoHuella"), "01")
    _add_sub(alta, _sf("Huella"), data.fingerprint)

    return etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", pretty_print=True
    )


def build_cancellation_xml(data: CancellationData) -> bytes:
    """Genera XML de anulación de factura según XSD de AEAT."""
    root = etree.Element(
        _slr("RegFactuSistemaFacturacion"), nsmap=NSMAP
    )

    _build_header(root, data.issuer_nif, data.issuer_name)

    reg_factura = etree.SubElement(
        root, _slr("RegistroFactura")
    )
    anulacion = etree.SubElement(
        reg_factura, _sf("RegistroAnulacion")
    )

    _add_sub(anulacion, _sf("IDVersion"), "1.0")

    # IDFactura (baja)
    id_factura = etree.SubElement(anulacion, _sf("IDFactura"))
    _add_sub(
        id_factura, _sf("IDEmisorFacturaAnulada"), data.issuer_nif
    )
    _add_sub(
        id_factura,
        _sf("NumSerieFacturaAnulada"),
        data.serial_number,
    )
    _add_sub(
        id_factura,
        _sf("FechaExpedicionFacturaAnulada"),
        data.issue_date,
    )

    if data.no_prior_record:
        _add_sub(anulacion, _sf("SinRegistroPrevio"), "S")
    if data.prior_rejection:
        _add_sub(anulacion, _sf("RechazoPrevio"), "S")

    _build_chaining(anulacion, data.previous)
    _build_software(anulacion, data.software)

    _add_sub(
        anulacion,
        _sf("FechaHoraHusoGenRegistro"),
        data.generation_timestamp,
    )
    _add_sub(anulacion, _sf("TipoHuella"), "01")
    _add_sub(anulacion, _sf("Huella"), data.fingerprint)

    return etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", pretty_print=True
    )


def validate_xml(xml_bytes: bytes) -> list[str]:
    """Valida XML contra los XSD de AEAT. Devuelve lista de errores."""
    schema_file = SCHEMAS_DIR / "SuministroLR.xsd"
    schema_doc = etree.parse(str(schema_file))
    schema = etree.XMLSchema(schema_doc)
    doc = etree.fromstring(xml_bytes)
    if schema.validate(doc):
        return []
    return [str(e) for e in schema.error_log]  # type: ignore[attr-defined]
