# Contributing

Install Python 3.10+, create a virtual environment, and install the project.
On Kali/Debian, install `python3-venv` and `python3-full` if the `venv` module
is missing:

```bash
sudo apt update
sudo apt install python3-venv python3-full
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pytest
```

Keep pip inside the virtual environment to avoid the PEP 668
`externally-managed-environment` error. `python3.11` is optional; use the
available `python3` executable.

Keep implementation changes under `cryql/`. Add focused tests for new
behavior and document security-sensitive changes.
