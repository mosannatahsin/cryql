# CryQL

CryQL is an evidence-driven GraphQL schema intelligence CLI for endpoints
where introspection may be unavailable. It combines safe introspection,
artifact ingestion, and bounded validation-based recovery while preserving
evidence and uncertainty in its output. See [`docs/usage.md`](docs/usage.md)
and [`docs/architecture.md`](docs/architecture.md).

## Installation

CryQL supports Python 3.11+:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
python -m cryql --help
```

For editable development installs, use `python -m pip install -e .`.

## CLI

```bash
python -m cryql -d https://example.test/graphql -o schema.json
cryql -d https://example.test/graphql --format sdl -o schema.graphql
```

Use `--allow-private` only for an explicitly authorized local lab target.
Headers and cookies are accepted with repeated `-H NAME:VALUE` and
`--cookie NAME:VALUE` options. If introspection is disabled, use bounded
validation recovery explicitly:

```bash
python -m cryql -d https://example.test/graphql --recovery \
  --wordlist words.txt -o recovered.json --format evidence
```

See [`benchmarks/README.md`](benchmarks/README.md) for reproducible
synthetic-lab measurements.

## Support and security

For questions or issues, use the [CryQL issue tracker](https://github.com/mosannatahsin/cryql/issues).
Security reports should follow [`SECURITY.md`](SECURITY.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development and testing guidance.
