"""Bind cached AMM attempts to the selected baseline and retained evidence."""
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            result.update(block)
    return result.hexdigest()


def tree(root):
    """Include nested inputs and internal SDK links without following link cycles."""
    root = Path(root).resolve()
    result = {}
    if not root.exists():
        return result

    def visit(directory, ancestors):
        real = directory.resolve()
        if not real.is_relative_to(root) or real in ancestors:
            raise RuntimeError('cache input directory link escapes or cycles: ' + str(directory))
        for path in sorted(directory.iterdir()):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                if not path.resolve().is_relative_to(root):
                    raise RuntimeError('cache input link escapes: ' + str(path))
                # The vendor SDK includes intentional dangling debugger links.
                # Preserve their spelling; real internal targets are inventoried
                # at their ordinary tree paths, without traversing aliases.
                result[relative] = {'symlink': os.readlink(path)}
            elif path.is_dir():
                visit(path, ancestors | {real})
            elif path.is_file() and path.resolve().is_relative_to(root):
                result[relative] = {'sha256': sha(path), 'mode': path.stat().st_mode & 0o777}
            else:
                raise RuntimeError('unsupported cache input: ' + str(path))
    visit(root, set())
    return result


def context(swarm, here, baseline, reader, want_disasm):
    implementations = [here / name for name in ('try_sell.py', 'native_build.py',
                        'sell_score.py', 'workspace_recipe.py', 'cache_inputs.py',
                        'metadata-map.json', 'ordered.ld')]
    build_environment = {key: value for key, value in os.environ.items()
                         if key.startswith('CARGO_PROFILE_RELEASE_') or key in
                         ('RUSTC_BOOTSTRAP', 'SOURCE_DATE_EPOCH', 'MACOSX_DEPLOYMENT_TARGET', 'SDKROOT')}
    return {'schema': 'amm-cache-inputs-v2', 'baseline': tree(baseline),
            'implementation': {p.name: sha(p) for p in implementations},
            'elf_reader_sha256': sha(reader), 'sdk': tree(swarm / 'infra/sdk-native'),
            'original_sha256': sha(swarm / 'infra/original/deployed.so'),
            'build_environment': build_environment, 'disasm': want_disasm}


def outputs(entry, swarm):
    out = Path(entry['out_dir']).resolve()
    if not out.is_relative_to((swarm / 'lanes').resolve()):
        raise ValueError('cached output is outside the lanes')
    names = ['sell.rs', 'build.log', 'build-record.json']
    if entry['status'] != 'build_failed':
        names += ['candidate.so', 'symbols.so']
    if entry['inputs']['context']['disasm'] and entry['status'] != 'build_failed':
        names += ['sell-align.diff', 'sell-original.s', 'sell-candidate.s']
    for name in names:
        path = out / name
        if path.is_symlink() or path.resolve().parent != out:
            raise ValueError('cached artifact must be a regular retained output')
    return {name: sha(out / name) for name in names}


def admitted(entry, key, key_doc, swarm):
    try:
        if entry['key'] != key or entry['inputs'] != key_doc:
            return False
        if entry['status'] not in ('build_failed', 'scored', 'GOAL_SELL_RAW_EQUAL'):
            return False
        actual = outputs(entry, swarm)
        if actual != entry['output_sha256']:
            return False
        if entry['status'] != 'build_failed':
            if (actual['candidate.so'] != entry['candidate_sha256'] or
                    actual['symbols.so'] != entry['unstripped_sha256']):
                return False
        return True
    except (OSError, KeyError, TypeError, ValueError):
        return False


def publish(path, entry):
    temporary = path.with_name('.' + path.name + '.tmp-' + entry['attempt_id'])
    try:
        temporary.write_text(json.dumps(entry, indent=1, sort_keys=True) + '\n')
        if path.exists():
            previous = path.parent / 'previous'
            previous.mkdir(exist_ok=True)
            path.rename(previous / (path.stem + '-' + entry['attempt_id'] + '.json'))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
