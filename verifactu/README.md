# verifactu

Librería Python pura para cumplimiento de VeriFactu (Real Decreto 1007/2023).
Sin dependencias de frameworks.

## ¿Qué es VeriFactu?

VeriFactu es el sistema de verificación de facturas establecido por el
Real Decreto 1007/2023 y desarrollado por la Orden HAC/1177/2024.
Obliga a que el software de facturación garantice la integridad, trazabilidad
e inmutabilidad de los registros fiscales.

### Plazos de obligatoriedad

- **Sociedades (IS):** 1 de enero de 2027
- **Autónomos (IRPF):** 1 de julio de 2027

### Requisitos principales

1. **Cadena de integridad (hash):** Cada factura genera un fingerprint SHA-256
   que incluye los datos de la factura y el fingerprint de la factura anterior,
   formando una cadena inmutable. Si se altera cualquier registro, la cadena
   se rompe.

2. **Código QR:** Cada factura debe incluir un código QR con una URL de
   verificación de la AEAT, permitiendo a cualquiera comprobar la validez
   del registro.

3. **Envío a la AEAT:** Los registros se envían a la Agencia Tributaria
   mediante SOAP con certificado digital (mutual TLS). Hay dos modalidades:
   - *VeriFactu:* envío automático a la AEAT en tiempo real.
   - *No VeriFactu:* el software cumple los requisitos pero no envía
     automáticamente (el contribuyente puede enviar después).

4. **XML según XSD de la AEAT:** Los registros se generan en formato XML
   siguiendo los esquemas XSD oficiales publicados por la AEAT
   (`SuministroLR` / `RegFactuSistemaFacturacion`).

5. **Inmutabilidad:** Una vez enviada una factura, no se puede modificar.
   Solo se puede anular mediante un registro de anulación (`RegistroAnulacion`).

### Concatenación del fingerprint (Orden HAC/1177/2024)

```
IDEmisorFactura + NumSerieFactura + FechaExpedicionFactura +
TipoFactura + CuotaTotal + ImporteTotal +
Huella_RegistroAnterior + FechaHoraHusoGenRegistro
```

El resultado se calcula con SHA-256 sobre la cadena codificada en UTF-8.
Para la primera factura de la cadena, `Huella_RegistroAnterior` queda vacío.

## Módulos

- `hash.py` — Cálculo del fingerprint SHA-256 según Orden HAC/1177/2024.
  Implementa la concatenación oficial para la cadena de integridad de registros.
- `constants.py` — Tipos de factura (StrEnum), URLs de la AEAT y constantes del algoritmo.

## Módulos planificados

- `qr.py` — Generación de código QR con URL de verificación de la AEAT.
- `xml_builder.py` — Generación de XML y validación contra XSD de la AEAT.
- `aeat_client.py` — Cliente SOAP para el envío de registros a la AEAT.

## Uso

```python
from verifactu.hash import compute_fingerprint

fingerprint = compute_fingerprint(
    issuer_nif="B12345678",
    serial_number="FAC-2027-001",
    issue_date="01-01-2027",
    invoice_type="F1",
    tax_amount="210.00",
    total_amount="1210.00",
    previous_fingerprint="",  # vacío para la primera factura de la cadena
    generation_timestamp="2027-01-01T10:00:00+01:00",
)
```

## Tests

```bash
uv run pytest verifactu/
```
