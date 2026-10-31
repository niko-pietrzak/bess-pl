import hashlib
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from bess.ingest import timestamp
from bess.ingest.timestamp import (
    TSAS,
    _children,
    build_request,
    certifi_root,
    parse_response,
    request_stamp,
)

FIXTURES = Path(__file__).parent / "fixtures" / "tsa"
DATA = (FIXTURES / "manifest.json").read_bytes()  # recorded live on 31.10.2026


def openssl3() -> str | None:
    for candidate in ("/opt/homebrew/bin/openssl", "/usr/local/bin/openssl", "openssl"):
        path = shutil.which(candidate)
        if path:
            version = subprocess.run([path, "version"], capture_output=True, text=True).stdout
            if version.startswith("OpenSSL 3"):
                return path
    return None


class Reply:
    def __init__(self, body):
        self.body = body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.mark.parametrize("tsa", ["digicert", "sectigo"])
def test_parse_recorded_response(tsa):
    token = parse_response((FIXTURES / f"{tsa}.tsr").read_bytes())
    assert token.status == 0
    assert token.digest == hashlib.sha256(DATA).digest()
    assert (
        datetime(2026, 10, 31, 23, tzinfo=UTC) < token.gen_time < datetime(2026, 11, 1, tzinfo=UTC)
    )
    assert token.nonce is not None
    assert len(token.certs) >= 3


def test_request_structure():
    digest = bytes(range(32))
    req = _children(_children(build_request(digest, 2**63 - 1))[0].content)
    assert [n.tag for n in req] == [0x02, 0x30, 0x02, 0x01]
    assert _children(req[1].content)[1].content == digest
    assert int.from_bytes(req[2].content, "big") == 2**63 - 1
    assert req[2].content[0] < 0x80  # positive INTEGER


def test_request_stamp_accepts_matching_token(monkeypatch):
    tsr = (FIXTURES / "digicert.tsr").read_bytes()
    monkeypatch.setattr(timestamp.secrets, "randbits", lambda _: parse_response(tsr).nonce)
    name, url, anchors = TSAS[0]
    s = request_stamp(name, url, anchors, DATA, lambda req, timeout: Reply(tsr))
    assert s.ok and s.tsr == tsr
    assert s.chain_pem.startswith(certifi_root("DigiCert Trusted Root G4"))


def test_request_stamp_rejects_other_data_or_nonce():
    tsr = (FIXTURES / "digicert.tsr").read_bytes()
    name, url, anchors = TSAS[0]
    s = request_stamp(name, url, anchors, DATA, lambda req, timeout: Reply(tsr))
    assert not s.ok and s.error == "imprint or nonce mismatch"  # random nonce differs
    s = request_stamp(name, url, anchors, b"other", lambda req, timeout: Reply(tsr))
    assert not s.ok


def test_anchor_roots_are_in_certifi():
    for _, _, anchors in TSAS:
        for label in anchors:
            assert certifi_root(label), label


@pytest.mark.skipif(openssl3() is None, reason="needs OpenSSL 3")
@pytest.mark.parametrize("tsa", ["digicert", "sectigo"])
def test_openssl_verifies_recorded_token(tsa, tmp_path, monkeypatch):
    tsr = (FIXTURES / f"{tsa}.tsr").read_bytes()
    monkeypatch.setattr(timestamp.secrets, "randbits", lambda _: parse_response(tsr).nonce)
    name, url, anchors = next(t for t in TSAS if t[0] == tsa)
    s = request_stamp(name, url, anchors, DATA, lambda req, timeout: Reply(tsr))
    (tmp_path / "chain.pem").write_text(s.chain_pem)
    (tmp_path / "token.tsr").write_bytes(tsr)
    out = subprocess.run(
        [
            openssl3(),
            "ts",
            "-verify",
            "-data",
            str(FIXTURES / "manifest.json"),
            "-in",
            str(tmp_path / "token.tsr"),
            "-CAfile",
            str(tmp_path / "chain.pem"),
        ],
        capture_output=True,
        text=True,
    )
    assert "Verification: OK" in out.stdout, out.stderr
