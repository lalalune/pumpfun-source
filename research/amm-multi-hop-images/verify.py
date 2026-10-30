#!/usr/bin/env python3
"""Verify the retained PumpSwap control and candidate images used by the multi-hop packets.

Each image must decompress to the stripped hash and size recorded in its
retained build provenance, and the candidate provenance must name the control
image as its comparison control.
"""
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IMAGES = {
    "control": "7a300434dced61413bde10788594b427d5649563e0223efcf09e6b214aff7ad3",
    "candidate": "d17a657baf5cc19736a924c41e75424604411ddbe9f6e72cddf41ab72a695007",
}


def fail(message):
    print(f"FAIL: {message}")
    sys.exit(1)


def main():
    stripped = {}
    for name, expected in IMAGES.items():
        image = gzip.decompress((ROOT / f"{name}.so.gz").read_bytes())
        provenance = json.loads((ROOT / f"{name}-build-provenance.json").read_text())
        strip = provenance["strip"]
        if hashlib.sha256(image).hexdigest() != expected:
            fail(f"{name} image hash")
        if strip["stripped_sha256"] != expected or strip["repeat_stripped_sha256"] != expected:
            fail(f"{name} provenance stripped hash")
        if strip["stripped_bytes"] != len(image):
            fail(f"{name} provenance stripped size")
        stripped[name] = expected
    candidate = json.loads((ROOT / "candidate-build-provenance.json").read_text())
    if candidate["baseline"]["stripped_sha256"] != stripped["control"]:
        fail("candidate provenance does not name the control image")
    print("PASS: control and candidate images match their retained build provenance")


if __name__ == "__main__":
    main()
