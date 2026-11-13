# Contributing

Install Python 3.11+, create a virtual environment, and install the project:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest
```

Keep implementation changes under `cryql/`. Add focused tests for new
behavior and document security-sensitive changes.
