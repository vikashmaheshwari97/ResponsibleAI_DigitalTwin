# Build Validation — 0.5.0 Local Feature-Complete

This package was validated before packaging.

## Static validation

- Full Python syntax compilation: **PASS**
- Legacy development-secret scan across source/config: **PASS**
- `.env` absent from distribution: **PASS**
- Python cache/bytecode removed from distribution before packaging: **PASS**
- No Alembic migration beyond `005_twin_snapshots`: **PASS**

## Automated tests in the packaging runtime

```text
10 passed, 2 skipped
```

The two skipped tests are dependency-coupled tests whose imports require `bcrypt` / `psycopg` / `streamlit`. Those packages are declared in the project requirements and are installed by GitHub Actions before `pytest -q`, so CI executes them normally.

Validated tests include the full FastAPI contract matrix:

| Scenario | Vulnerable profile | Secure profile |
|---|---:|---:|
| SCN-001 BOLA | HTTP 200 | HTTP 403 |
| SCN-002 expired token | HTTP 200 | HTTP 401 |
| SCN-003 malformed payload | HTTP 201 | HTTP 422 |
| SCN-004 rate control | final HTTP 200 | final HTTP 429 |

## Evidence bundle smoke test

A synthetic report bundle was generated with the database-coupled repository layer stubbed only for the packaging smoke test.

- PDF/JSON/CSV ZIP generation: **PASS**
- `manifest.json` generation: **PASS**
- SHA-256 verification of all bundled evidence files: **PASS**

## Local runtime validation still required

After copying this package into the existing PyCharm project, run:

```bash
python -m pip install --upgrade -r requirements.txt
python -m pip install --upgrade -r requirements-dev.txt
pytest -q
python scripts/validate_local_release.py
python scripts/validate_local_release.py --exercise-sandbox
```

The local validator uses the user's actual Docker, PostgreSQL, `.env`, and Ollama runtime. University of Tartu server deployment is intentionally not part of this package.
