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

**Alta (RegistroAlta):**
```
IDEmisorFactura=valor&NumSerieFactura=valor&FechaExpedicionFactura=valor&
TipoFactura=valor&CuotaTotal=valor&ImporteTotal=valor&
Huella=valor&FechaHoraHusoGenRegistro=valor
```

**Anulación (RegistroAnulacion):**
```
IDEmisorFacturaAnulada=valor&NumSerieFacturaAnulada=valor&
FechaExpedicionFacturaAnulada=valor&Huella=valor&
FechaHoraHusoGenRegistro=valor
```

Formato: `campo=valor` separados por `&` (sin URL-encoding).
SHA-256 sobre la cadena en UTF-8. Resultado en hexadecimal mayúsculas.
Para el primer registro de la cadena, `Huella` queda vacío (pero el campo se incluye).

## Módulos

- `hash.py` — Cálculo del fingerprint SHA-256 según Orden HAC/1177/2024.
  Dos funciones: `compute_registration_fingerprint()` (alta) y
  `compute_cancellation_fingerprint()` (anulación), con nombres de campo
  diferentes según el tipo de registro.
- `constants.py` — Tipos de factura (StrEnum), URLs de la AEAT y constantes del algoritmo.
- `qr.py` — Generación de código QR con URL de verificación de la AEAT.
- `xml_builder.py` — Generación de XML (`RegistroAlta` y `RegistroAnulacion`)
  y validación contra los XSD oficiales de la AEAT.
- `aeat_client.py` — Cliente SOAP para el envío de registros a la AEAT
  (mutual TLS, SOAP 1.1, parseo de respuesta, conversión PFX→PEM).
- `schemas/` — XSD oficiales de la AEAT (SuministroLR, SuministroInformacion,
  RespuestaSuministro).

## Uso

```python
from verifactu.hash import compute_registration_fingerprint

fingerprint = compute_registration_fingerprint(
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
