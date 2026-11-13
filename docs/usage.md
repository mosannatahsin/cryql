# CryQL usage

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
