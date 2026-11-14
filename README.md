# CryQL

CryQL is an evidence-driven GraphQL schema intelligence CLI for endpoints
where introspection may be unavailable. It combines safe introspection,
artifact ingestion, and bounded validation-based recovery while preserving
evidence and uncertainty in its output. See [`docs/usage.md`](docs/usage.md)
and [`docs/architecture.md`](docs/architecture.md).

## Installation

CryQL supports Python 3.10 through Python 3.14. A virtual environment only
isolates Python packages; it does not install CryQL by itself. Clone the
repository, change into its root, and verify that `pyproject.toml` is present
before installing:

```bash
git clone https://github.com/mosannatahsin/cryql.git
cd cryql
test -f pyproject.toml && test -d cryql || {
  echo "Run this command from the CryQL repository root." >&2
  exit 1
}
pwd
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
python -m cryql --help
cryql --help
```

If the clone is somewhere else, install it with its absolute path instead of
using `.`:

```bash
python -m pip install /path/to/cryql
```

On Kali/Debian systems, install the virtual-environment support first if
`python3 -m venv` reports that `ensurepip` is unavailable:

```bash
sudo apt update
sudo apt install python3-venv python3-full
```

Do not install CryQL into the system interpreter. This avoids Debian's
`externally-managed-environment` (PEP 668) error. If you prefer an isolated
application install, `pipx install .` also provides the `cryql` command.

For editable development installs, activate the venv and use
`python -m pip install -e .`.

### Troubleshooting

- `python3.11: command not found`: use `python3`; CryQL does not require the
  `python3.11` executable specifically.
- `python3 -m venv .venv` cannot run `ensurepip`: install `python3-venv` (and
  `python3-full` when your distribution splits standard-library components).
- `externally-managed-environment`: create and activate `.venv`, then run pip
  through that environment's `python`; do not use `sudo pip`.
- `ERROR: Directory '.' is not installable`: `.` means the current directory,
  so change into the cloned CryQL repository root or use
  `python -m pip install /path/to/cryql`.
- `No module named cryql`: a venv alone does not install CryQL. Install the
  repository into that venv, then activate it or invoke its interpreter
  directly (`.venv/bin/python -m cryql --help`).
- `cryql: command not found`: install CryQL into the active venv and ensure its
  `bin` directory is on `PATH`, or use `.venv/bin/cryql --help`.
- `cryql is a package and cannot be directly executed`: update the checkout and
  reinstall it; current releases include `cryql/__main__.py`, so both
  `python -m cryql --help` and `cryql --help` are supported.

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
