"""
infra/rsa.py — just enough RSA to verify a webhook signature, in the stdlib.

PayPal signs webhook deliveries with RSA-SHA256 over a canonical string. Verifying
that needs three things this project cannot `pip install`:

  1. read a public key out of a PEM (either a bare SPKI or a full X.509 cert),
  2. turn the signature back into an integer with `pow`,
  3. check the PKCS#1 v1.5 padding is exactly what a SHA-256 digest produces.

It is ~90 lines because that is all it is. The part that is easy to get wrong is
(1): a certificate contains *two* RSA algorithm identifiers, and the first one —
inside `signature` — is not the key. Taking the first OID you find verifies
signatures against an algorithm name, which always fails, or worse.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

RSA_OID = b"\x06\x09\x2a\x86\x48\x86\xf7\x0d\x01\x01\x01"
SHA256_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


class KeyError_(ValueError):
    """The PEM did not contain an RSA public key we could read."""


# -- the smallest DER reader that can do the job ---------------------------
def _tlv(data: bytes, i: int = 0) -> tuple[int, bytes, int, int]:
    """(tag, content, next_index, header_length) at offset i."""
    tag = data[i]
    length = data[i + 1]
    header = 2
    if length & 0x80:
        n = length & 0x7F
        if n == 0 or n > 4:
            raise KeyError_("DER: unsupported length")
        length = int.from_bytes(data[i + 2:i + 2 + n], "big")
        header = 2 + n
    start = i + header
    end = start + length
    if end > len(data):
        raise KeyError_("DER: truncated")
    return tag, data[start:end], end, header


def _elements(data: bytes) -> list[tuple[int, bytes, int]]:
    out, i = [], 0
    while i < len(data):
        tag, content, nxt, _h = _tlv(data, i)
        out.append((tag, content, i))
        i = nxt
    return out


def _int(content: bytes) -> int:
    return int.from_bytes(content.lstrip(b"\x00") or b"\x00", "big")


def _rsa_from_sequence(seq: bytes) -> tuple[int, int]:
    parts = _elements(seq)
    if len(parts) < 2 or parts[0][0] != 0x02 or parts[1][0] != 0x02:
        raise KeyError_("not an RSA key sequence")
    return _int(parts[0][1]), _int(parts[1][1])


def _from_spki(der: bytes) -> tuple[int, int]:
    _t, spki, _i, _h = _tlv(der, 0)                 # SubjectPublicKeyInfo
    parts = _elements(spki)
    if len(parts) < 2 or RSA_OID not in spki:
        raise KeyError_("SPKI is not an RSA key")
    tag, bits = parts[-1][0], parts[-1][1]
    if tag != 0x03:
        raise KeyError_("SPKI has no BIT STRING")
    _t, inner, _i, _h = _tlv(bits[1:], 0)           # skip unused-bits octet
    return _rsa_from_sequence(inner)


def _from_certificate(der: bytes) -> tuple[int, int]:
    """
    Walk TBSCertificate properly: [0] version, serial, **signature**, issuer,
    validity, subject, SubjectPublicKeyInfo. The signature algorithm at position 3
    carries the same OID as the key and must be skipped.
    """
    _t, cert, _i, _h = _tlv(der, 0)                  # Certificate
    tbs_content = _elements(cert)[0][1]              # tbsCertificate
    fields = _elements(tbs_content)
    j = 0
    if fields and fields[0][0] == 0xA0:              # explicit version
        j = 1
    for _skip in range(3):                           # serial, signature, issuer
        j += 1
    for _skip in range(2):                           # validity, subject
        j += 1
    tag, spki = fields[j][0], fields[j][1]
    if tag != 0x30:
        raise KeyError_("certificate: expected SPKI")
    return _from_spki(_wrap(spki))


def _wrap(spki_content: bytes) -> bytes:
    """Re-encode a SEQUENCE around content already parsed out."""
    return b"\x30" + _len(len(spki_content)) + spki_content


def _len(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(raw)]) + raw


def parse_public_key(pem: str) -> tuple[int, int]:
    """PEM `PUBLIC KEY` (SPKI) or `CERTIFICATE` (X.509) → (n, e)."""
    body = "".join(line.strip() for line in (pem or "").splitlines()
                   if "-----" not in line)
    if not body:
        raise KeyError_("empty PEM")
    try:
        der = base64.b64decode(body, validate=False)
    except Exception:
        raise KeyError_("PEM is not base64") from None
    if "BEGIN CERTIFICATE" in pem:
        return _from_certificate(der)
    return _from_spki(der)


# -- the verification -------------------------------------------------------
def verify_sha256(message: bytes, signature: bytes, n: int, e: int) -> bool:
    """RSASSA-PKCS1-v1_5 with SHA-256. Returns False, never raises."""
    try:
        k = (n.bit_length() + 7) // 8
        if not signature or len(signature) != k:
            return False
        em = pow(int.from_bytes(signature, "big"), e, n).to_bytes(k, "big")
        digest_info = SHA256_PREFIX + hashlib.sha256(message).digest()
        pad = k - len(digest_info) - 3
        if pad < 8:                                    # 8 is the spec's minimum
            return False
        expected = b"\x00\x01" + b"\xff" * pad + b"\x00" + digest_info
        return hmac.compare_digest(em, expected)
    except (ValueError, TypeError):
        return False
