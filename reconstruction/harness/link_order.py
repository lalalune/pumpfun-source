"""Pinned link order for the main Pump cdylib: a build input, like the AMM/Fees/Mayhem ordered.ld.

A crate may carry `link/ordered.ld`. fastbuild then links the root cdylib with that script
instead of the SBF target's default script (`sbf_default.ld`, byte-identical to the
`rustc-sbf-linkfile.ld` that platform-tools v1.44 rustc writes). The replacement may only
reorder input sections: it must equal the default script except that the `.text`,
`.rodata` and `.data.rel.ro` rules may each become a list of input-section selectors that
ends with the default catch-all pattern. No symbols, assignments, fill bytes, alignment or
data commands are admitted, so the output is still exactly the compiler's sections,
linked by the same rust-lld, only placed in a different order.

Hooks (entry points `pump_link_rustc.py`, `pump_link_lld.py`):
- RUSTC_WRAPPER: for the root cdylib only, append `-C linker=pump_link_lld.py` (an untracked
  rustc option: object code and every dependency are unchanged), then run the next wrapper.
- linker: check the incoming script is the default one, swap in the pinned script, write a
  receipt and a link map beside it, and exec the real rust-lld with otherwise identical arguments.
"""
import hashlib
import json
import os
import re
import sys
import tomllib
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
    default = DEFAULT.read_text() if default is None else default
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
    manifest = tomllib.loads((Path(crate) / 'Cargo.toml').read_text())
    lib_name = manifest.get('lib', {}).get('name') or manifest['package']['name'].replace('-', '_')
    counts = check_script(script.read_text())
    lld = sorted(Path(rustc).parents[1].glob('lib/rustlib/*/bin/rust-lld'))
    if len(lld) != 1:
        raise ValueError('expected one host rust-lld beside ' + str(rustc))
    env = {'RUSTC_WRAPPER': str(H / 'pump_link_rustc.py'),
            'PUMP_LINK_NEXT_WRAPPER': str(H / 'pump_physical_source_wrapper.py'),
            'PUMP_LINK_ROOT_CRATE': lib_name,
            'PUMP_LINK_SCRIPT': str(script.resolve()),
            'PUMP_LINK_SCRIPT_SHA256': sha(script),
            'PUMP_LINK_LLD': str(lld[0]),
            'PUMP_LINK_RECEIPT': str(receipt),
            'PUMP_LINK_MAP': str(Path(receipt).with_name('link.map'))}
    return env, {'script': SCRIPT.as_posix(), 'script_sha256': env['PUMP_LINK_SCRIPT_SHA256'],
                 'selectors': counts, 'lld_sha256': sha(lld[0])}


def rustc_args(argv, env):
    """Command for the next wrapper; adds the linker hook only to the root cdylib compilation."""
    rustc, args = argv[1], list(argv[2:])
    name = args[args.index('--crate-name') + 1] if '--crate-name' in args else None
    kinds = [args[i + 1] for i, value in enumerate(args[:-1]) if value == '--crate-type']
    if name == env['PUMP_LINK_ROOT_CRATE'] and 'cdylib' in kinds:
        if any(a.startswith(('linker=', '-Clinker=')) for a in args):
            raise ValueError('root crate already sets a linker')
        args += ['-C', 'linker=' + str(H / 'pump_link_lld.py')]
    return [sys.executable, env['PUMP_LINK_NEXT_WRAPPER'], rustc, *args]


def rustc_main(argv, env):
    command = rustc_args(argv, env)
    os.execv(command[0], command)


def lld_args(args, env):
    """Linker arguments with the default script replaced; raises unless exactly one default script."""
    default = DEFAULT.read_text()
    script = env['PUMP_LINK_SCRIPT']
    if sha(script) != env['PUMP_LINK_SCRIPT_SHA256']:
        raise ValueError('pinned link script changed during the build')
    check_script(Path(script).read_text(), default)
    out, seen, i = [], 0, 0
    while i < len(args):
        arg = args[i]
        if arg in ('-T', '--script'):
            if Path(args[i + 1]).read_text() != default:
                raise ValueError('unexpected target link script ' + args[i + 1])
            out += [arg, script]; seen += 1; i += 2
            continue
        if arg.startswith('--script=') or (arg.startswith('-T') and arg != '-T'):
            raise ValueError('unsupported script argument ' + arg)
        out.append(arg); i += 1
    if seen != 1:
        raise ValueError('expected exactly one target link script, saw %d' % seen)
    if env.get('PUMP_LINK_MAP'):  # evidence only: a map file does not change the output
        out.append('-Map=' + env['PUMP_LINK_MAP'])
    return out


def lld_main(argv, env):
    args = lld_args(list(argv[1:]), env)
    lld = env['PUMP_LINK_LLD']
    Path(env['PUMP_LINK_RECEIPT']).write_text(json.dumps({
        'script': env['PUMP_LINK_SCRIPT'], 'script_sha256': env['PUMP_LINK_SCRIPT_SHA256'],
        'default_script_sha256': sha(DEFAULT), 'lld': lld, 'lld_sha256': sha(lld),
        'forwarded': args}, indent=1) + '\n')
    os.execv(lld, [lld, *args])
