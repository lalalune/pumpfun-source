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
        "a2a7c4f0e2b0bcdad4ceb3548d834f9a239942d1cdb0d5c694944233e7bef96d",
        "9f2073520c319ca8db15d683da038590cd2da16304d1550e95648b89b3213083",
        "4f32c8013e9359d32d2685860cc0c3628c2c44887d89cecf94609f360e038b73",
        "038de3a138c8fb2b55a7ef870064b4f1cd39f104f45a182b49d44d05f8654bd5",
        "646aadd3a8eb0f8da7131da81461921fef7e9b1f0928d988a51998599e390471",
        "b6e945c08aac13ebd5c4411b9f7ce21fecd8daf6753eb432769189b96a820e5a",
        "149d5d3dd0a9765f0da71abcdda42169d4e06ee0ed1bd64e355b8d3978aa8969",
        "a1c2eb7cdd0fa0077d809d4936868bf17127de3ef7d4d52e686ab59ce913502e",
        "0b15933c655b8c6fd8d3504ffa18415f26d67cb58eeee9416e35941a8cb292db",
        "8cd4023f5d5b69e7ed8146abaae6a913368b9a4d03feda354698ce8bb36b1cd2",
    },
    "scripts/window_elf_reader.py": {
        "df1c2b1369e996146f05bd9f9714b112a013550fa25d1206f6b29e3ef079dd74",
        "b1b47d11c2f19868bb9ba9671f3591821dd552a401ebe5dff0bdf11cb926fc51",
        "247700e9930d5e53daf93a50888ae1e5429f74ccb19155e7a205f72ee21d5883",
        "bc2f71be6e043735dda5c6d43e5e3ed614f405c6e15adefe47d6e0a74d94d10a",
        "b00c2c491dce839aba97b19fd9007da5eaa99902968d88e8c44bb071bb0c9c1c",
        "d3b57510531d7977110e73474cf89310b68bf6705d134ffb3bc759e18d30bedd",
        "bf3ae0bb3c3d57638b22d379b44674be5098c9a9a59243f38fb2d04e081df55c",
    },
    "scripts/deep_disassembly.py": {
        "9bc109b8d2fbe0c0becb4b82199d7fbf2fa6048c6f54f0eb3f9cb489985ffdc2",
        "d8ef84d3cc6fbb1a43161242bebd7d5158fbebabd70837feb867bb653645e310",
        "6203189864fd7c2a9cd8ad7363f78542c2f419b6f4388f416d9286f0ff67932f",
        "d2b9873473bbeea33bb5d953d0c6385b1127d81aedba652bb1b82de636849aa5",
        "47cfa5cf9b7e271ad2ea399220930ad238713b465b030181f74a1990a34275ce",
        "17b35e60802ef12f0c452bcb65d2f74e0325ae310dc0041cd764edc8667ed97c",
        "c71540059cb76cf4b6cca866113395f11092134d9110201e38aaa36475f360af",
        "a91c80af30d1fa9bdb217f1450e8856b98c2873e57502aef48b06cfe6602e854",
        "0275d4680af3b239ac4bca442685357d4dff2a59b2f633a58fed768980682bab",
        "6ca5d4711d64b8af061d9becd71eff289dd4b1aa40f5ba9d234ef7675e098efc",
        "6e6f0fb542cf1e870897c0f82cbaa9e496b1a6bb1888ead197d8b747cf683ad5",
        "b8e952be9a97a02c29769cc2e1c2d54ba526e149baaf40485e57008d5ad0460e",
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
