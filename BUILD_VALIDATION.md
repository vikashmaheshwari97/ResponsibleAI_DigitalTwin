# Build Validation

The generated Roadmap 1–4 upgrade was checked before packaging.

## Static validation

- Full Python syntax compilation: PASS
- Secret scan for the old development values: PASS (no matches)
- `.env` absent from distribution: PASS
- Python cache/bytecode absent from distribution: PASS

## Unit tests

- Scenario registry tests: PASS
- Analytics duration helper tests: PASS
- Total: 5 tests passed

## SecureMessenger scenario contract tests

Using FastAPI TestClient:

| Scenario | Vulnerable profile | Secure profile |
|---|---:|---:|
| SCN-001 BOLA | 200 | 403 |
| SCN-002 expired token | 200 | 401 |
| SCN-003 malformed payload | 201 | 422 |
| SCN-004 rate control | final 200 | final 429 |

## Report export smoke test

- PDF generation produced a valid `%PDF` document: PASS
- Complete evidence ZIP generation produced a valid ZIP archive: PASS

Full Docker/Streamlit/PostgreSQL end-to-end validation must still be run in the user's local development environment after copying the upgrade because that environment contains the existing persistent PostgreSQL volume, Docker runtime, and local Ollama service.
