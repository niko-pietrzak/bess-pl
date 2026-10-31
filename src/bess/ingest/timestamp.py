"""RFC 3161 time stamps for slot manifests: proof that the data existed before the cutoff.

A token from a Time Stamping Authority (TSA) binds the manifest's SHA-256 to the TSA's clock.
If its time is before the cutoff, the snapshot cannot contain anything published later.
Only the fields we check are parsed here; the signature is verified offline with
`openssl ts -verify -data _manifest.json -in <tsa>.tsr -CAfile <tsa>.chain.pem`
(OpenSSL 3; the LibreSSL shipped with macOS rejects some of these chains).
"""

import base64
import hashlib
import secrets
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

import certifi

# Tried in order until two tokens are granted. DigiCert and Sectigo are independent CAs;
# the others are fallbacks. Anchor: the root in certifi that completes the embedded chain;
# it goes first in the chain file, or OpenSSL follows DigiCert's cross-certificate to a
# root that is no longer in certifi.
TSAS = [
    (
        "digicert",
        "http://timestamp.digicert.com",
        ("DigiCert Trusted Root G4",),
    ),
    ("sectigo", "http://timestamp.sectigo.com", ("USERTrust RSA Certification Authority",)),
    ("globalsign", "http://timestamp.globalsign.com/tsa/r6advanced1", ()),
    ("freetsa", "https://freetsa.org/tsr", ()),
]
REQUIRED = 2

_SHA256 = bytes.fromhex("300d06096086480165030402010500")  # AlgorithmIdentifier sha256


def _tlv(tag: int, content: bytes) -> bytes:
    n = len(content)
    if n < 0x80:
        length = bytes([n])
    else:
        raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
        length = bytes([0x80 | len(raw)]) + raw
    return bytes([tag]) + length + content


def build_request(digest: bytes, nonce: int) -> bytes:
    """DER TimeStampReq: v1, SHA-256 imprint, nonce, certReq=true."""
    imprint = _tlv(0x30, _SHA256 + _tlv(0x04, digest))
    nonce_bytes = nonce.to_bytes(nonce.bit_length() // 8 + 1, "big")  # leading 0: positive
    body = _tlv(0x02, b"\x01") + imprint + _tlv(0x02, nonce_bytes) + _tlv(0x01, b"\xff")
    return _tlv(0x30, body)


@dataclass
class _Node:
    tag: int
    content: bytes
    raw: bytes


def _children(der: bytes) -> list[_Node]:
    out, pos = [], 0
    while pos < len(der):
        tag, n = der[pos], der[pos + 1]
        head = 2
        if n & 0x80:
            size = n & 0x7F
            n = int.from_bytes(der[pos + 2 : pos + 2 + size], "big")
            head += size
        end = pos + head + n
        out.append(_Node(tag, der[pos + head : end], der[pos:end]))
        pos = end
    return out


@dataclass
class Token:
    status: int  # 0 granted, 1 granted with modifications, 2+ rejected
    gen_time: datetime | None = None
    digest: bytes | None = None
    nonce: int | None = None
    certs: list[bytes] = field(default_factory=list)


def _generalized_time(raw: bytes) -> datetime:
    text = raw.decode().rstrip("Z")
    base, _, fraction = text.partition(".")
    ts = datetime.strptime(base, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
    return ts.replace(microsecond=int((fraction or "0").ljust(6, "0")[:6]))


def parse_response(der: bytes) -> Token:
    """Read status, genTime, imprint, nonce and embedded certificates of a TimeStampResp."""
    resp = _children(_children(der)[0].content)
    token = Token(status=int.from_bytes(_children(resp[0].content)[0].content, "big"))
    if len(resp) < 2:
        return token
    content_info = _children(resp[1].content)
    signed_data = _children(_children(content_info[1].content)[0].content)
    encap = _children(signed_data[2].content)
    tst_der = _children(encap[1].content)[0].content
    tst = _children(_children(tst_der)[0].content)
    token.digest = _children(tst[2].content)[1].content
    token.gen_time = _generalized_time(tst[4].content)
    token.nonce = next((int.from_bytes(n.content, "big") for n in tst[5:] if n.tag == 0x02), None)
    for node in signed_data[3:]:
        if node.tag == 0xA0:  # certificates [0] IMPLICIT SET OF Certificate
            token.certs = [c.raw for c in _children(node.content)]
    return token


def to_pem(cert_der: bytes) -> str:
    b64 = base64.b64encode(cert_der).decode()
    lines = [b64[i : i + 64] for i in range(0, len(b64), 64)]
    return "-----BEGIN CERTIFICATE-----\n" + "\n".join(lines) + "\n-----END CERTIFICATE-----\n"


def certifi_root(label: str) -> str | None:
    """PEM of the root with this label in certifi's (Mozilla) bundle."""
    text = open(certifi.where()).read()
    marker = f'# Label: "{label}"'
    if marker not in text:
        return None
    block = text.split(marker, 1)[1]
    start = block.index("-----BEGIN CERTIFICATE-----")
    end = block.index("-----END CERTIFICATE-----") + len("-----END CERTIFICATE-----")
    return block[start:end] + "\n"


@dataclass
class Stamp:
    tsa: str
    url: str
    ok: bool
    error: str | None = None
    gen_time: datetime | None = None
    tsr: bytes = b""
    chain_pem: str = ""


def request_stamp(name: str, url: str, anchors: tuple[str, ...], data: bytes, opener) -> Stamp:
    digest = hashlib.sha256(data).digest()
    nonce = secrets.randbits(63)
    req = urllib.request.Request(
        url,
        data=build_request(digest, nonce),
        headers={"Content-Type": "application/timestamp-query", "User-Agent": "bess-pl"},
        method="POST",
    )
    try:
        with opener(req, timeout=30) as resp:
            tsr = resp.read()
        token = parse_response(tsr)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, IndexError) as e:
        return Stamp(name, url, False, f"{type(e).__name__}: {e}")
    if token.status not in (0, 1):
        return Stamp(name, url, False, f"status {token.status}", tsr=tsr)
    if token.digest != digest or token.nonce != nonce:
        return Stamp(name, url, False, "imprint or nonce mismatch", tsr=tsr)
    roots = [certifi_root(label) or "" for label in anchors]
    chain = "".join(roots) + "".join(to_pem(c) for c in token.certs)
    return Stamp(name, url, True, None, token.gen_time, tsr, chain)


def stamp(data: bytes, opener: Callable, tsas=TSAS, required: int = REQUIRED) -> list[Stamp]:
    """Ask TSAs in order until `required` tokens are granted; returns every attempt."""
    out: list[Stamp] = []
    for name, url, anchors in tsas:
        if sum(s.ok for s in out) >= required:
            break
        out.append(request_stamp(name, url, anchors, data, opener))
    return out
