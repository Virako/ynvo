# ynvo

Django app for generating invoices with VeriFactu compliance.

## Architecture

```
invoices/
├── verifactu/            ← Pure Python library (no Django dependency)
├── django_verifactu/     ← Django app: InvoiceRecord model, manager, admin
├── ynvo/                 ← Invoice app: models, services, admin, templates
└── pyproject.toml
```

- `verifactu` is standalone: SHA-256 fingerprint chain, QR generation, XML builder, AEAT SOAP client.
- `django_verifactu` provides persistence for VeriFactu records. Only depends on Django and `verifactu`.
- `ynvo` is the consumer: connects invoices with VeriFactu records via services.
- `import-linter` enforces these architectural boundaries in CI.

## VeriFactu

Integration with Spain's VeriFactu system (Real Decreto 1007/2023) for invoice
verification. Currently operating in **No VeriFactu** mode: the app generates
the fingerprint chain, QR codes and XML records, but does not send them
automatically to AEAT. Records can be submitted manually via AEAT's web portal
using the taxpayer's browser certificate.

The AEAT SOAP client is implemented and tested for future automatic submission.
See [verifactu/README.md](verifactu/README.md) for details.

## Development

```bash
uv run pytest                    # run all tests
uv run pytest --cov              # with coverage
uv run import-linter             # check architectural boundaries
uv run ruff check .              # linting
```
