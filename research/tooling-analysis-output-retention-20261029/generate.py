#!/usr/bin/env python3
"""Publish the reviewed program analysis only to a new output directory."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HELPERS = {
    "scripts/analyze_program.py": {
        "b6e945c08aac13ebd5c4411b9f7ce21fecd8daf6753eb432769189b96a820e5a",
        "149d5d3dd0a9765f0da71abcdda42169d4e06ee0ed1bd64e355b8d3978aa8969",
    },
    "scripts/window_elf_reader.py": {
        "247700e9930d5e53daf93a50888ae1e5429f74ccb19155e7a205f72ee21d5883",
        "bc2f71be6e043735dda5c6d43e5e3ed614f405c6e15adefe47d6e0a74d94d10a",
    },
}
PROGRAMS = ("pump", "pump_amm", "pump_fees", "mayhem")


def helper_hashes(root):
    result = {}
    for name, accepted in HELPERS.items():
        digest = hashlib.sha256((root / name).read_bytes()).hexdigest()
        if digest not in accepted:
            raise ValueError(f"Unreviewed analysis helper: {name}")
        result[name] = digest
    return result


def generate(program, output, root=ROOT):
    if program not in PROGRAMS:
        raise ValueError("Unsupported captured program")
    root = Path(root).resolve()
    output = Path(output).absolute()
    if os.path.lexists(output):
        raise FileExistsError(f"Analysis output already exists: {output}")
    helpers = helper_hashes(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Generate beside the destination so publication stays on one filesystem.
    # A failed analysis or packet check never leaves a partial final packet.
    with tempfile.TemporaryDirectory(prefix=f".{output.name}-stage-", dir=output.parent) as temporary:
        packet = Path(temporary) / "packet"
        result = subprocess.run(
            [sys.executable, "-E", "-X", "utf8", str(root / "scripts/analyze_program.py"),
             "--program", program, "--output", str(packet)],
            cwd=root, capture_output=True, text=True, encoding="utf-8", check=True,
        )
        subprocess.run(
            [sys.executable, "-E", "-X", "utf8", str(packet / "verify.py")],
            cwd=root, capture_output=True, text=True, encoding="utf-8", check=True,
        )
        if helper_hashes(root) != helpers:
            raise ValueError("Analysis helpers changed during generation")
        if os.path.lexists(output):
            raise FileExistsError(f"Analysis output appeared during generation: {output}")
        os.rename(packet, output)
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program", choices=PROGRAMS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        generate(args.program, args.output)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Analysis was not published: {error}\n")
    print(f"Published verified {args.program} analysis to {args.output}")


if __name__ == "__main__":
    main()
