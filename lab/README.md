# CryQL local lab

The synthetic server uses only the Python standard library:

```bash
python lab/server.py --port 8765
python -m cryql -d http://127.0.0.1:8765/graphql --allow-private
python -m cryql -d http://127.0.0.1:8765/graphql --allow-private \
  --recovery --wordlist cryql/wordlist.txt -o recovered.json
```

Use `--no-introspection`, `--no-suggestions`, `--delay SECONDS`, or
`--rate-limit N` to exercise bounded failure handling. The schema and responses
are synthetic and contain no user data.
