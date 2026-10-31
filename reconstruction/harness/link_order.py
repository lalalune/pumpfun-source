"""Pinned link order for the main Pump cdylib: a build input, like the AMM/Fees/Mayhem ordered.ld.

A crate may carry `link/ordered.ld`. fastbuild then links the root cdylib with that script
instead of the SBF target's default script (`sbf_default.ld`, byte-identical to the
`rustc-sbf-linkfile.ld` that platform-tools v1.44 rustc writes). The replacement may only
reorder input sections: it must equal the default script except that the `.text`,
`.rodata` and `.data.rel.ro` rules may each become a list of input-section selectors that
ends with the default catch-all pattern. No symbols, assignments, fill bytes, alignment or
data commands are admitted, so the output is still exactly the compiler's sections,
linked by the same rust-lld, only placed in a different order.

Hooks (entry points `pump_link_rustc.sh`, `pump_link_lld.sh`, using the configuring Python):
- RUSTC_WRAPPER: for the root cdylib only, append `-C linker=pump_link_lld.sh` (an untracked
  rustc option: object code and every dependency are unchanged), then run the next wrapper.
- linker: reject response-file inputs, check the incoming script is the default one, swap in the
  pinned script, write a receipt and a link map beside it, and run the real rust-lld until it exits with otherwise
  identical arguments.
"""
import hashlib
import json
import os
import re
import sys
import tomllib
import subprocess
import tempfile
from pathlib import Path

H = Path(__file__).resolve().parent
DEFAULT = H / 'sbf_default.ld'
SCRIPT = Path('link/ordered.ld')  # relative to the crate directory
SECTIONS = {'.text': 'text', '.rodata': 'rodata', '.data.rel.ro': 'rodata'}
FILEPAT = r'\*[A-Za-z0-9_.*:-]*'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rule(name):
    return f'  {name} : {{ *({name}*) }} :{SECTIONS[name]}'


def check_script(text, default=None):
    """Return {output section: selector count}; raise ValueError if `text` is not admitted."""
    default = DEFAULT.read_text(encoding='utf-8') if default is None else default
    # Line endings are linker whitespace. Compare their LF view without
    # rewriting the pinned bytes passed to lld or recorded in the receipt.
    text, default = text.replace('\r\n', '\n'), default.replace('\r\n', '\n')
    counts, rest, pieces = {}, text, []
    for name in SECTIONS:
        if default.count(rule(name)) != 1:
            raise ValueError('default script lacks rule ' + rule(name))
    # Walk the default script, matching each section rule either verbatim or as a block.
    pos = 0
    for name in SECTIONS:
        line = rule(name)
        i = default.index(line, pos)
        pieces.append(default[pos:i])
        pieces.append(name)
        pos = i + len(line)
    pieces.append(default[pos:])
    for piece in pieces:
        if piece not in SECTIONS:
            if not rest.startswith(piece):
                raise ValueError('script differs from the default outside the ordered rules')
            rest = rest[len(piece):]
            continue
        name = piece
        if rest.startswith(rule(name)):
            rest = rest[len(rule(name)):]
            counts[name] = 0
            continue
        opening = f'  {name} : {{\n'
        closing = f'    *({name}*)\n  }} :{SECTIONS[name]}'
        if not rest.startswith(opening) or closing not in rest:
            raise ValueError('malformed ordered rule for ' + name)
        inner, rest = rest[len(opening):].split(closing, 1)
        lines = inner.split('\n')[:-1] if inner.endswith('\n') else None
        if lines is None:
            raise ValueError('malformed ordered rule for ' + name)
        esc = re.escape(name)
        exact = re.compile(rf'^    {FILEPAT}\("{esc}\.[^"\s()]+"\)$')
        glob = re.compile(rf'^    {FILEPAT}\({esc}\*\)$')
        for selector in lines:
            if not (exact.fullmatch(selector) or glob.fullmatch(selector)):
                raise ValueError('unadmitted linker statement: ' + selector)
        if len(lines) != len(set(lines)):
            raise ValueError('duplicate selector in ' + name)
        counts[name] = len(lines)
    if rest:
        raise ValueError('trailing statements after the default script')
    return counts


def configure(crate, rustc, receipt):
    """(environment, record) for a compile when `crate` carries a pinned link script, else ({}, None)."""
    script = Path(crate) / SCRIPT
    if not script.is_file():
        return {}, None
    manifest = tomllib.loads((Path(crate) / 'Cargo.toml').read_text(encoding='utf-8'))
    lib_name = manifest.get('lib', {}).get('name') or manifest['package']['name'].replace('-', '_')
    script_bytes = script.read_bytes()
    counts = check_script(script_bytes.decode('utf-8'))
    lld = sorted(Path(rustc).parents[1].glob('lib/rustlib/*/bin/rust-lld'))
    if len(lld) != 1:
        raise ValueError('expected one host rust-lld beside ' + str(rustc))
    env = {'RUSTC_WRAPPER': str(H / 'pump_link_rustc.sh'),
            'PUMP_RECON_PYTHON': sys.executable,
            'PUMP_LINK_NEXT_WRAPPER': str(H / 'pump_physical_source_wrapper.py'),
            'PUMP_LINK_ROOT_CRATE': lib_name,
            'PUMP_LINK_SCRIPT': str(script.resolve()),
            'PUMP_LINK_SCRIPT_SHA256': hashlib.sha256(script_bytes).hexdigest(),
            'PUMP_LINK_LLD': str(lld[0]),
            'PUMP_LINK_RECEIPT': str(receipt),
            'PUMP_LINK_MAP': str(Path(receipt).with_name('link.map'))}
    return env, {'script': SCRIPT.as_posix(), 'script_sha256': env['PUMP_LINK_SCRIPT_SHA256'],
                 'selectors': counts, 'lld_sha256': sha(lld[0])}


def rustc_args(argv, env):
    """Command for the next wrapper; adds the linker hook only to the root cdylib compilation."""
    rustc, args = argv[1], list(argv[2:])
    options = args[:args.index('--')] if '--' in args else args
    def values(flag):
        result = []
        for index, value in enumerate(options):
            if value == flag:
                if index + 1 == len(options):
                    raise ValueError(flag + ' requires a value')
                result.append(options[index + 1])
            elif value.startswith(flag + '='):
                result.append(value[len(flag) + 1:])
        return result
    names = values('--crate-name')
    name = names[0] if names else None
    kinds = [kind for value in values('--crate-type') for kind in value.split(',')]
    if name == env['PUMP_LINK_ROOT_CRATE'] and 'cdylib' in kinds:
        codegen = values('--codegen') + values('-C')
        codegen += [value[2:] for value in options if value.startswith('-C') and len(value) > 2 and not value.startswith('-C=')]
        if any(value.partition('=')[0] == 'linker' for value in codegen):
            raise ValueError('root crate already sets a linker')
        position = args.index('--') if '--' in args else len(args)
        args[position:position] = ['-C', 'linker=' + str(H / 'pump_link_lld.sh')]
    return [sys.executable, env['PUMP_LINK_NEXT_WRAPPER'], rustc, *args]


def rustc_main(argv, env):
    command = rustc_args(argv, env)
    if os.name == 'nt':
        # The Windows CRT execv joins argv without the quoting provided by
        # subprocess and does not preserve the child's exit status here.
        raise SystemExit(subprocess.run(command).returncode)
    os.execv(command[0], command)


def lld_args(args, env, *, script_path=None, script_bytes=None, default_bytes=None):
    """Linker arguments with the default script replaced; raises unless exactly one default script."""
    default = (DEFAULT.read_bytes() if default_bytes is None else default_bytes).decode('utf-8').replace('\r\n', '\n')
    raw = Path(env['PUMP_LINK_SCRIPT']).read_bytes() if script_bytes is None else script_bytes
    script = env['PUMP_LINK_SCRIPT'] if script_path is None else str(script_path)
    if hashlib.sha256(raw).hexdigest() != env['PUMP_LINK_SCRIPT_SHA256']:
        raise ValueError('pinned link script changed during the build')
    check_script(raw.decode('utf-8'), default)
    out, seen, i = [], 0, 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('@'):
            raise ValueError('response-file linker input unsupported: ' + arg)
        if arg in ('-T', '-script', '--script'):
            if Path(args[i + 1]).read_text() != default:
                raise ValueError('unexpected target link script ' + args[i + 1])
            out += [arg, script]; seen += 1; i += 2
            continue
        if arg.startswith(('--script=', '-script=')) or (arg.startswith('-T') and arg != '-T'):
            raise ValueError('unsupported script argument ' + arg)
        out.append(arg); i += 1
    if seen != 1:
        raise ValueError('expected exactly one target link script, saw %d' % seen)
    if env.get('PUMP_LINK_MAP'):  # evidence only: a map file does not change the output
        out.append('-Map=' + env['PUMP_LINK_MAP'])
    return out


def lld_main(argv, env):
    raw = Path(env['PUMP_LINK_SCRIPT']).read_bytes()
    default = DEFAULT.read_bytes()
    # The mutable crate pathname is never forwarded to the linker. Keep the
    # private checked copy alive until the child exits, then remove it.
    with tempfile.TemporaryDirectory(prefix='pump-link-script-') as temporary:
        script = Path(temporary) / 'ordered.ld'
        script.write_bytes(raw)
        args = lld_args(list(argv[1:]), env, script_path=script, script_bytes=raw, default_bytes=default)
        lld = env['PUMP_LINK_LLD']
        Path(env['PUMP_LINK_RECEIPT']).write_text(json.dumps({
            'script': env['PUMP_LINK_SCRIPT'], 'script_sha256': hashlib.sha256(raw).hexdigest(),
            'default_script_sha256': hashlib.sha256(default).hexdigest(), 'lld': lld, 'lld_sha256': sha(lld),
            'forwarded': args}, indent=1) + '\n', encoding='utf-8', newline='\n')
        return subprocess.run([lld, *args]).returncode
