#!/usr/bin/env bash
set -euo pipefail

python scripts/migrate_database.py
exec python -m streamlit run app.py \
  --server.address=0.0.0.0 \
  --server.port=8501 \
  --server.headless=true
