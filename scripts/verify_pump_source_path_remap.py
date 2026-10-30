"""Verify a controlled Pump-only Rust source-path remap build offline."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O.")

import gzip
import hashlib
import json
import struct
import subprocess
from pathlib import Path

from elftools.elf.elffile import ELFFile


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "repro/pump/path-remap-fortyeight"
TARGET = ROOT / "evidence/original/pump/deployed.so"
BASE = ROOT / "repro/pump/quote-control-fortyeight/candidate.so"
BASE_BUILD = ROOT / "repro/pump/quote-control-fortyeight/build-comparison.json"
TRIAL = FOLDER / "candidate.so"
WRAPPER = ROOT / "scripts/pump_rustc_source_path_wrapper.sh"
OUT = FOLDER / "verification.json"
SOURCE_BASE = "4ffe8bd88761059693e481ae972443c10204f7af"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def section(path, name):
    with path.open("rb") as stream:
        return ELFFile(stream).get_section_by_name(name).data()


def locations(path, name):
    encoded = name.encode()
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        rodata = elf.get_section_by_name(".rodata")
        relro = elf.get_section_by_name(".data.rel.ro")
        relocations = elf.get_section_by_name(".rel.dyn")
        assert rodata and relro and relocations
        ro, data = rodata.data(), relro.data()
        offset = ro.find(encoded)
        assert offset >= 0 and ro.find(encoded, offset + 1) < 0
        virtual = rodata["sh_addr"] + offset
        pointer = (virtual << 32).to_bytes(8, "little")
        relocated = {entry["r_offset"] for entry in relocations.iter_relocations()}
        rows = []
        start = 0
        while (index := data.find(pointer, start)) != -1:
            start = index + 1
            if relro["sh_addr"] + index not in relocated or index + 24 > len(data):
                continue
            length = struct.unpack_from("<Q", data, index + 8)[0]
            if length not in (len(encoded), len(encoded) + 1):
                continue
            line, column = struct.unpack_from("<II", data, index + 16)
            rows.append({"line": line, "column": column, "stored_path_length": length,
                         "trailing_nul_included": length == len(encoded) + 1})
        return rows


def normalized_bpf(data):
    output = bytearray(data)
    cursor = 0
    while cursor + 8 <= len(output):
        opcode = output[cursor]
        if opcode in (0x18, 0x85):
            output[cursor + 4:cursor + 8] = bytes(4)
        if opcode == 0x18 and cursor + 16 <= len(output):
            output[cursor + 12:cursor + 16] = bytes(4)
            cursor += 16
        else:
            cursor += 8
    return output


def main():
    target = TARGET.read_bytes()
    base = BASE.read_bytes()
    trial = TRIAL.read_bytes()
    saved = json.loads(BASE_BUILD.read_text())
    built = json.loads((FOLDER / "build-comparison.json").read_text())
    attempt = json.loads((FOLDER / "build-attempt.json").read_text())
    assert attempt["returncode"] == 0 and attempt["source_unchanged"]
    assert saved["source_sha256"] == built["source_sha256"]
    assert len(saved["source_sha256"]) == 35
    # This trial predates later Pump handlers. Verify its compiler inputs from
    # the immutable ancestor commit instead of the evolving checkout source.
    subprocess.run(["git", "merge-base", "--is-ancestor", SOURCE_BASE, "HEAD"],
                   cwd=ROOT, check=True)
    assert all(sha(subprocess.check_output(
        ["git", "show", f"{SOURCE_BASE}:{path}"], cwd=ROOT)) == digest
        for path, digest in saved["source_sha256"].items())
    assert saved["rustc_sha256"] == built["rustc_sha256"]
    assert saved["selected_toolchain"] == built["selected_toolchain"] == "v1.44"
    assert sha(base) == saved["comparison"]["candidate_sha256"]
    assert sha(trial) == built["comparison"]["candidate_sha256"]
    assert sha(target) == saved["comparison"]["original_sha256"] == \
        built["comparison"]["original_sha256"]
    assert sha(gzip.decompress((FOLDER / "build.log.gz").read_bytes())) == \
           built["build_log_sha256"]
    base_text = section(BASE, ".text")
    trial_text = section(TRIAL, ".text")
    assert len(base_text) == len(trial_text) == 1_365_320
    base_loc = locations(BASE, "src/create_v2.rs")
    trial_loc = locations(TRIAL, "programs/pump/src/create_v2.rs")
    target_loc = locations(TARGET, "programs/pump/src/create_v2.rs")
    assert len(base_loc) == len(trial_loc) == 10 and len(target_loc) == 4
    assert [row["line"] for row in base_loc] == [row["line"] for row in trial_loc]
    assert all(row["stored_path_length"] == 30 and not row["trailing_nul_included"]
               for row in trial_loc + target_loc)
    raw_differences = sum(a != b for a, b in zip(base_text, trial_text))
    normalized_differences = sum(a != b for a, b in zip(
        normalized_bpf(base_text), normalized_bpf(trial_text)))
    assert raw_differences == 7_476 and normalized_differences == 265
    report = {
        "scope": "Saved v1.44 candidate with Pump-crate-only Rustc path remap. Build/source/compiler hashes and relocation-backed source locations are checked. The RUSTC_WRAPPER environment is a declared build input, not independently attested by build-comparison.json. No deployed byte match or historical flag attribution.",
        "base_candidate_sha256": sha(base),
        "remapped_candidate_sha256": sha(trial),
        "target_sha256": sha(target),
        "source_files_checked": len(saved["source_sha256"]),
        "source_verification_commit": SOURCE_BASE,
        "rustc_sha256": built["rustc_sha256"],
        "wrapper_sha256": sha(WRAPPER.read_bytes()),
        "base_elf_bytes": len(base), "remapped_elf_bytes": len(trial),
        "base_text_bytes": len(base_text), "remapped_text_bytes": len(trial_text),
        "raw_text_difference_positions": raw_differences,
        "normalized_text_difference_positions": normalized_differences,
        "base_create_v2_lines": [row["line"] for row in base_loc],
        "remapped_create_v2_lines": [row["line"] for row in trial_loc],
        "target_create_v2_lines": [row["line"] for row in target_loc],
        "remapped_path_matches_target": True,
        "remapped_source_lines_match_target": False,
        "byte_identical_deployment": False,
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"path_match": True,
                      "source_lines_match": False,
                      "trial_sha256": report["remapped_candidate_sha256"]}))


if __name__ == "__main__":
    main()
