# CryQL usage

## Installation

CryQL supports Python 3.10 through Python 3.14. A virtual environment does not
install CryQL; install the repository into it from the repository root:

```bash
git clone https://github.com/mosannatahsin/cryql.git
cd cryql
test -f pyproject.toml && test -d cryql || {
  echo "Run this command from the CryQL repository root." >&2
  exit 1
}
pwd
python3 --version
sudo apt update
sudo apt install python3-venv python3-full
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
python -m cryql --help
cryql --help
```

When you are not in the clone, use its absolute path:

```bash
python -m pip install /path/to/cryql
```

The virtual environment is required on distributions enforcing PEP 668
(`externally-managed-environment`). Do not use system-wide pip; `pipx install .`
is another safe option for an isolated CLI install.

If `python -m pip install .` says that the directory is not installable, `.`
refers to your current working directory, not automatically to the CryQL
clone. Change to the clone root or use the absolute-path command above.

## Usage

```bash
python -m cryql -d https://example.test/graphql -o schema.json
cryql -d https://example.test/graphql --format sdl -o schema.graphql
```

Use `--allow-private` only for an explicitly authorized local lab target.
Headers and cookies are accepted with repeated `-H NAME:VALUE` and
`--cookie NAME:VALUE` options. `--artifacts` can be repeated for local
JavaScript, GraphQL operation text, HAR/Burp JSON, or introspection JSON.

If introspection is disabled, use bounded validation recovery explicitly:

```bash
python -m cryql -d https://example.test/graphql --recovery \
  --wordlist words.txt -o recovered.json --format evidence
```

Recovery follows accepted field and validation errors into bounded nested
selections and records required arguments when the server discloses them.
Suggestions remain candidates, and a complete schema is not promised when the
endpoint does not disclose enough behavior.
