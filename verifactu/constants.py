from enum import StrEnum


class InvoiceType(StrEnum):
    F1 = "F1"  # Factura (art. 6, 7.2 y 7.3 del RD 1619/2012)
    F2 = "F2"  # Factura simplificada (art. 6.1.d y 7.1 del RD 1619/2012)
    F3 = "F3"  # Factura emitida en sustitución de facturas simplificadas
    R1 = "R1"  # Factura rectificativa (art. 80.1, 80.2 y 80.6 LIVA)
    R2 = "R2"  # Factura rectificativa (art. 80.3 LIVA)
    R3 = "R3"  # Factura rectificativa (art. 80.4 LIVA)
    R4 = "R4"  # Factura rectificativa (resto)
    R5 = "R5"  # Factura rectificativa en facturas simplificadas


AEAT_PRODUCTION_URL = "https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQR"
AEAT_TEST_URL = "https://prewww2.aeat.es/wlpl/TIKE-CONT/ValidarQR"
