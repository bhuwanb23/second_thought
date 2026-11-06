"""The cryptography under the webhook check, tested on its own.

A 512-bit key, signed for real with a private exponent. It is not secure and is
not meant to be: it exists so PKCS#1 v1.5 padding and DER parsing are exercised
for real rather than mocked.
"""

import base64
import hashlib
import json
import unittest
import zlib

from secondthought.infra.rsa import KeyError_, parse_public_key, verify_sha256
from secondthought.infra.webhook import canonical

N = int("cedcdd728c7af6ce0a6670d2d59fee104869361d641de648b0162d85c68d4acd"
        "8e58de986e6bfebc4e5aac1344c49a241412940688b6b71fb505e69a2abfa01f", 16)
D = int("4f87826bc3ae92ac6c3b2e2d208c380e72886091b427fa9cff75c752a31f371e"
        "5640bdffb40da8001fb6fda5151c492a1835177786426f048996b25fb9a483e1", 16)
E = 65537
K = (N.bit_length() + 7) // 8
PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")
RSA_OID = bytes.fromhex("06092a864886f70d010101")
SHA256_RSA_OID = bytes.fromhex("06092a864886f70d01010b")
WEBHOOK_ID = "WH-TEST-0001"
CERT_URL = "https://api.sandbox.paypal.com/v1/notifications/certs/CERT-360caa42"


# -- minimal DER encoder, so the test can hand the parser a real structure ----
def _len(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(raw)]) + raw


def der(tag: int, content: bytes) -> bytes:
    return bytes([tag]) + _len(len(content)) + content


def integer(value: int) -> bytes:
    body = value.to_bytes((value.bit_length() + 7) // 8 or 1, "big")
    if body[0] & 0x80:
        body = b"\x00" + body
    return der(0x02, body)


def spki(n: int = N, e: int = E) -> bytes:
    key = der(0x30, integer(n) + integer(e))
    return der(0x30, der(0x30, RSA_OID + der(0x05, b"")) + der(0x03, b"\x00" + key))


def pem(der_bytes: bytes, label: str = "PUBLIC KEY") -> str:
    body = base64.b64encode(der_bytes).decode()
    lines = [body[i:i + 64] for i in range(0, len(body), 64)]
    return f"-----BEGIN {label}-----\n" + "\n".join(lines) + f"\n-----END {label}-----\n"


def certificate(spki_der: bytes = None) -> bytes:
    """A structurally valid Certificate whose signature algorithm is *not* the key."""
    spki_der = spki_der or spki()
    tbs = der(0x30, b"".join([
        der(0xA0, integer(2)),                              # [0] version
        integer(0x1234),                                    # serial
        der(0x30, SHA256_RSA_OID + der(0x05, b"")),          # signature — decoy
        der(0x30, b""),                                     # issuer
        der(0x30, b""),                                     # validity
        der(0x30, b""),                                     # subject
        spki_der,                                           # the real key
    ]))
    return der(0x30, tbs + der(0x30, SHA256_RSA_OID + der(0x05, b""))
               + der(0x03, b"\x00" + b"\x11" * 64))


def sign(message: bytes) -> bytes:
    """Sign with the private exponent, exactly as PayPal's HSM would."""
    digest_info = PREFIX + hashlib.sha256(message).digest()
    em = b"\x00\x01" + b"\xff" * (K - len(digest_info) - 3) + b"\x00" + digest_info
    return pow(int.from_bytes(em, "big"), D, N).to_bytes(K, "big")


def headers(tid="TID-1", ttime="2026-11-04T10:00:00Z", body=b"", sig=None,
            cert_url=CERT_URL):
    return {"PAYPAL-TRANSMISSION-ID": tid, "PAYPAL-TRANSMISSION-TIME": ttime,
            "PAYPAL-TRANSMISSION-SIG": base64.b64encode(
                sign(canonical(tid, ttime, WEBHOOK_ID, body)) if sig is None else sig
            ).decode(),
            "PAYPAL-CERT-URL": cert_url,
            "PAYPAL-AUTH-ALGO": "SHA256withRSA"}


CERT_PEM = pem(certificate(), "CERTIFICATE")
EVENT = {"id": "WH-EVT-1", "event_type": "INVOICING.INVOICE.PAID",
         "resource": {"id": "INV2-TEST-0001"}}
BODY = json.dumps(EVENT).encode()


class Crypto(unittest.TestCase):
    def test_the_stdlib_verifies_a_real_signature(self):
        self.assertTrue(verify_sha256(b"message", sign(b"message"), N, E))

    def test_a_changed_byte_does_not_verify(self):
        self.assertFalse(verify_sha256(b"messagf", sign(b"message"), N, E))

    def test_a_truncated_signature_does_not_verify(self):
        self.assertFalse(verify_sha256(b"message", sign(b"message")[:-1], N, E))

    def test_garbage_does_not_raise_it_returns_false(self):
        for bad in (b"", b"\x00" * K, b"not-a-signature"):
            self.assertFalse(verify_sha256(b"message", bad, N, E))

    def test_the_crc_is_over_the_raw_bytes(self):
        raw = b'{"a": 1}'
        expected = f"TID|TIME|{WEBHOOK_ID}|{zlib.crc32(raw) & 0xFFFFFFFF}".encode()
        self.assertEqual(canonical("TID", "TIME", WEBHOOK_ID, raw), expected)

    def test_reformatting_the_json_changes_the_signed_message(self):
        self.assertNotEqual(canonical("T", "2026", WEBHOOK_ID, b'{"a":1}'),
                            canonical("T", "2026", WEBHOOK_ID, b'{"a": 1}'))


class KeyParsing(unittest.TestCase):
    def test_a_public_key_pem_gives_the_modulus_and_exponent(self):
        self.assertEqual(parse_public_key(pem(spki())), (N, E))

    def test_a_certificate_pem_skips_the_signature_algorithm_and_finds_the_key(self):
        """Both algorithm identifiers are present; the first one is a decoy."""
        self.assertIn(SHA256_RSA_OID, certificate())
        self.assertEqual(parse_public_key(CERT_PEM), (N, E))

    def test_a_certificate_with_a_non_rsa_key_fails_closed(self):
        ec_spki = der(0x30, der(0x30, bytes.fromhex("06072a8648ce3d0201")
                               + der(0x05, b"")) + der(0x03, b"\x00" + der(0x30, b"")))
        with self.assertRaises(KeyError_):
            parse_public_key(pem(certificate(ec_spki), "CERTIFICATE"))

    def test_empty_and_junk_pem_raise(self):
        for bad in ("", "-----BEGIN CERTIFICATE-----\n-----END CERTIFICATE-----",
                    "not a pem at all"):
            with self.assertRaises(KeyError_):
                parse_public_key(bad)


if __name__ == "__main__":
    unittest.main()
