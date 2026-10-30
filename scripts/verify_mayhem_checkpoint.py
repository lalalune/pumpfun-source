#!/usr/bin/env python3
"""Verify the exact maintained Mayhem source, hosted builds and signed corpus."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import zipfile

from analyze import elf_layout

ROOT = Path(__file__).resolve().parents[1]
PACKET = 'research/mayhem-canonical-promotion-20261028'
ORIGINAL_PAYLOAD_SHA256 = 'a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb'
MEANINGFUL_ELF_BYTES = 775416


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def verify_meaningful_elf(root, candidate_path):
    """Compare the selected stripped ELF to the authenticated capture's file bytes.

    The captured ProgramData allocation has a zero tail beyond its ELF extent.
    Those allocation bytes are excluded; every byte through the extent is included.
    """
    capture = root/'evidence/original/mayhem'
    receipt = json.loads((capture/'capture.json').read_text())
    original = (capture/'deployed.so').read_bytes()
    require(hashlib.sha256(original).hexdigest() == receipt['payload_sha256'] == ORIGINAL_PAYLOAD_SHA256,
            'Mayhem captured payload identity')
    require(len(original) == receipt['payload_bytes'], 'Mayhem captured allocation length')
    layout = elf_layout(original)
    require(layout['elf_extent'] == MEANINGFUL_ELF_BYTES and layout['trailing_all_zero'],
            'Mayhem captured meaningful ELF boundary')
    candidate = candidate_path.read_bytes()
    require(len(candidate) == MEANINGFUL_ELF_BYTES and candidate == original[:MEANINGFUL_ELF_BYTES],
            'Mayhem selected meaningful ELF bytes')
    return {'meaningful_elf_bytes': MEANINGFUL_ELF_BYTES,
            'excluded_zero_allocation_tail_bytes': layout['trailing_bytes'],
            'captured_payload_sha256': ORIGINAL_PAYLOAD_SHA256}


def verify(root=ROOT):
    root = Path(root).resolve()
    selected = json.loads((root/'repro/status.json').read_text())['mayhem']
    packet = root/PACKET
    require(sha(packet/'manifest.json') == selected['checkpoint_manifest_sha256'] == '352ff61d70e81bdb009bf23ca8effe14cd7789d86f13ea214ddbd381f802239e', 'Mayhem current packet seal')
    require(sha(packet/'selection.json') == selected['source_identity_report_sha256'] == '40878ee84e8d26d67f630979a9c3b7a8d023d1e3da397ac57eabbfcb6daaa29a', 'Mayhem selected source identity')
    report = module('current_mayhem_source',packet/'verify.py').verify(root)
    signatures = module('current_mayhem_signatures',packet/'verify_signatures.py').verify(packet)
    require(selected['candidate_artifact'] == PACKET+'/hosted/40770208958/candidate.so' and selected['candidate_symbols_artifact'] == PACKET+'/hosted/40770208958/symbols.so', 'Mayhem selected image paths')
    require(report['candidate_sha256'] == selected['candidate_sha256'] == sha(root/selected['candidate_artifact']), 'Mayhem literal selected image')
    require(report['symbols_sha256'] == selected['symbols_sha256'] == sha(root/selected['candidate_symbols_artifact']), 'Mayhem literal selected symbols')
    require(report['verified_source_is_canonical'] is True and report['fresh_windows_builds'] == 2 and report['meaningful_elf_bytes'] == 775416, 'Mayhem maintained exact build scope')
    meaningful = verify_meaningful_elf(root, root/selected['candidate_artifact'])
    require(selected['full_byte_equality'] is True and selected['validated_cases'] == 9592 and selected['validated_instruction_comparisons'] == 9595, 'Mayhem finite runtime scope')
    require(signatures['transactions'] == 20056 and signatures['signature_fields'] == selected['verified_transaction_signatures'] == 39062, 'Mayhem retained signature scope')
    log = selected['build_log_archive']
    with zipfile.ZipFile(root/log['path']) as archive:
        actual_log = archive.read(log['member'])
    require(hashlib.sha256(actual_log).hexdigest() == log['uncompressed_sha256'] and gzip.decompress((root/selected['build_log']).read_bytes()) == actual_log, 'Mayhem actual compiler log binding')
    return {'status':'PASS','program':'mayhem','candidate_sha256':report['candidate_sha256'],
            'symbols_sha256':report['symbols_sha256'],'current_source_verified':True,
            'meaningful_elf_equal':True,'meaningful_elf_identity':meaningful,
            'source_and_build':report,'signature_verification':signatures}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=ROOT)
    args = parser.parse_args()
    print(json.dumps(verify(args.repo),indent=2))
