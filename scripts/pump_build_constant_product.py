#!/usr/bin/env python3
"""Compile the arithmetic fragment from frozen source/compiler bytes.

Driver and target libraries remain in the configured toolchain. This binds an
arithmetic-fragment comparison, not a complete toolchain or program identity.
"""
import argparse, hashlib, io, json, pathlib, subprocess, tempfile
from elftools.elf.elffile import ELFFile
ROOT=pathlib.Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()
RANGE_START=0x880b0
RANGE_END=0x88908

def pinned_original(root):
    """Slice the retained original function only from the pinned capture.

    Python slicing never raises on a short or shifted image, so the whole-file
    SHA-256 is bound to the capture manifest first and the exact slice length
    is checked second; a report must never measure the wrong byte range.
    """
    raw=(root/'evidence/original/pump/deployed.so').read_bytes()
    manifest=json.loads((root/'evidence/original/pump/capture.json').read_text())
    expected=manifest.get('payload_sha256')
    if not expected or sha(raw)!=expected:
        raise SystemExit('captured pump deployed.so does not match its retained capture manifest')
    original=raw[RANGE_START:RANGE_END]
    if len(original)!=RANGE_END-RANGE_START:
        raise SystemExit('captured pump deployed.so is shorter than the pinned original function range')
    return original

def unchanged(path, expected, label):
    if sha(path.read_bytes()) != expected:
        raise ValueError(f'{label} changed during build')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--toolchain', type=pathlib.Path, required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    original = pinned_original(ROOT)
    rustc = args.toolchain.resolve() / 'rust/bin/rustc'
    source = ROOT / 'programs/pump/recovered/constant_product.rs'
    source_bytes, compiler_bytes = source.read_bytes(), rustc.read_bytes()
    source_hash, compiler_hash = sha(source_bytes), sha(compiler_bytes)
    obj = args.output.resolve() / 'constant_product.o'
    with tempfile.TemporaryDirectory(prefix='.compile-inputs-', dir=args.output) as temporary:
        staging = pathlib.Path(temporary).resolve()
        frozen_source = staging / 'src/constant_product.rs'
        frozen_source.parent.mkdir()
        frozen_source.write_bytes(source_bytes)
        frozen_source.chmod(0o444)
        frozen_rustc = staging / 'rust/bin/rustc'
        frozen_rustc.parent.mkdir(parents=True)
        frozen_rustc.write_bytes(compiler_bytes)
        frozen_rustc.chmod(rustc.stat().st_mode & 0o777)
        # rustc loads its driver and target libraries relative to rust/bin.
        # Keep that layout without writing into the configured toolchain.
        libraries = rustc.parent.parent / 'lib'
        if libraries.is_dir():
            (staging / 'rust/lib').symlink_to(libraries, target_is_directory=True)
        version = subprocess.check_output([str(frozen_rustc), '--version', '--verbose'], text=True)
        unchanged(frozen_rustc, compiler_hash, 'compiler snapshot')
        remap = f'--remap-path-prefix={frozen_source.parent}={source.parent}'
        command = [str(frozen_rustc), '--edition=2021', '--target', 'sbf-solana-solana',
                   '--crate-type', 'lib', '--emit=obj', '-C', 'opt-level=3', '-C',
                   'panic=abort', '-C', 'overflow-checks=yes', remap,
                   str(frozen_source), '-o', str(obj)]
        result = subprocess.run(command, text=True, capture_output=True)
        (args.output / 'build.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        result.check_returncode()
        unchanged(frozen_source, source_hash, 'source snapshot')
        unchanged(frozen_rustc, compiler_hash, 'compiler snapshot')
        unchanged(source, source_hash, 'source')
        unchanged(rustc, compiler_hash, 'rustc')
        object_bytes = obj.read_bytes()
        section = ELFFile(io.BytesIO(object_bytes)).get_section_by_name('.text.constant_product_output')
        if section is None:
            raise ValueError('compiled object lacks constant_product_output')
        compiled = section.data()
        locations = {str(frozen_rustc): '<snapshot>/rust/bin/rustc',
                     str(frozen_source): '<snapshot>/src/constant_product.rs',
                     str(obj): '<output>/constant_product.o',
                     remap: '--remap-path-prefix=<snapshot>/src=<repo>/programs/pump/recovered'}
        report = {
            'scope': 'Arithmetic semantics only. Error representation is a compact enum, not original Anchor allocation/metadata, so this fragment does not claim the historical ABI or complete function reconstruction. No original code enters compilation.',
            'source_sha256': source_hash, 'rustc_sha256': compiler_hash,
            'rustc_version': version, 'command': [locations.get(value, value) for value in command],
            'input_snapshot_scope': 'Private copies of source and rustc executable; driver and target libraries use the configured toolchain.',
            'object_sha256': sha(object_bytes),
            'original_function_start': RANGE_START, 'original_function_end': RANGE_END,
            'original_function_bytes': len(original), 'compiled_function_bytes': len(compiled),
            'original_function_sha256': sha(original), 'compiled_function_sha256': sha(compiled),
            'full_function_byte_equality': original == compiled, 'whole_program_byte_equality': None,
        }
    with (args.output / 'comparison.json').open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
