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
verification and submission to AEAT. See [verifactu/README.md](verifactu/README.md)
for details.

## Development

```bash
uv run pytest                    # run all tests
uv run pytest --cov              # with coverage
uv run import-linter             # check architectural boundaries
uv run ruff check .              # linting
```
