from __future__ import annotations

import gzip

from scripts.verify_backup import verify_backup


def test_verify_backup_accepts_gzip_postgresql_dump(tmp_path):
    path = tmp_path / "rai_twin_test.sql.gz"
    with gzip.open(path, "wb") as handle:
        handle.write(b"-- PostgreSQL database dump\nCREATE TABLE example(id integer);\n")

    result = verify_backup(path)
    assert result["gzip_valid"] is True
    assert result["looks_like_postgresql_dump"] is True
    assert result["decompressed_bytes"] > 0
    assert len(result["sha256"]) == 64
