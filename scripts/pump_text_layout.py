"""Optional, main-only .text input ordering and complete lld input receipts."""
import hashlib
import json
import subprocess
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULE = '  .text : { *(.text*) } :text'
FILEPAT = r'\*[A-Za-z0-9_.*:$+@/-]*'
SELECTOR = re.compile(r'^    ' + FILEPAT + r'\((?:"\.text[A-Za-z0-9_.$:+@/-]*"|\.text\*)\)$')
# lld also reads these long options with one dash, a spelling that
# declared_inputs and prepare_link do not otherwise recognize.
FILE_OPTIONS = ('--script', '--version-script', '--just-symbols', '--dynamic-list',
                '--retain-symbols-file', '--symbol-ordering-file',
                '--call-graph-ordering-file', '--export-dynamic-symbol-list', '--remap-inputs')
SUFFIXES = {'.o': 'object', '.obj': 'object', '.a': 'archive', '.rlib': 'archive',
            '.so': 'shared-object', '.dylib': 'shared-object', '.bc': 'bitcode'}
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(condition, message):
    """Fail closed under optimized Python, where assert statements vanish."""
    if not condition:
        raise AssertionError(message)


def check_script(default, script, data_certificate=None):
    if data_certificate:
        import pump_data_order
        script = pump_data_order.check_combined(script, pump_data_order.load_certificate(data_certificate))
    check(default.count(RULE) == 1, 'default script must contain exactly one .text rule')
    head, tail = default.split(RULE)
    opening, closing = head + '  .text : {\n', '\n    *(.text*)\n  } :text' + tail
    check(script.startswith(opening) and script.endswith(closing), 'replacement script must wrap the default .text rule')
    inner = script[len(opening):-len(closing)]
    lines = inner.split('\n') if inner else []
    check(all(SELECTOR.fullmatch(line) for line in lines), 'unexpected linker statement')
    check(len(lines) == len(set(lines)), 'duplicate selector')
    return len(lines)


def configure(order, out, sdk, crate_name, physical_wrapper, data_certificate=None):
    default = (HERE / 'pump_text_layout_default.ld').read_text()
    script = Path(order).read_text()
    count = check_script(default, script)
    certificate_copy = None
    if data_certificate:
        import pump_data_order
        certificate = pump_data_order.load_certificate(data_certificate)
        script = pump_data_order.render(script, certificate)
        certificate_copy = Path(out) / 'data-order-certificate.json'
    dest = Path(out) / 'ordered.ld'
    rustc_version = subprocess.check_output([str(Path(sdk) / 'rust/bin/rustc'), '-vV'], text=True)
    hosts = re.findall(r'^host: ([A-Za-z0-9_-]+)$', rustc_version, re.M)
    check(len(hosts) == 1, 'SDK rustc must report exactly one host triple')
    host = hosts[0]
    linker = Path(sdk) / f'rust/lib/rustlib/{host}/bin/rust-lld'
    check(linker.is_file(), 'SDK linker must be a file')
    files = [HERE / name for name in ['pump_text_layout.py', 'pump_text_layout_rustc.py',
             'pump_text_layout_linker.py', 'pump_text_layout_default.ld',
             'pump_text_layout_rustc.sh', 'pump_text_layout_linker.sh']]
    if data_certificate:
        files += [HERE / name for name in pump_data_order.implementation_hashes()]
    helper_sha256 = {str(p): sha(p) for p in files}
    external_wrapper_sha256 = sha(physical_wrapper)
    if certificate_copy:
        certificate_copy.write_bytes(Path(data_certificate).read_bytes())
    dest.write_text(script,encoding='utf-8',newline='\n')
    record = {'scope': 'Optional main-only compiler/link recipe; no original ELF input or byte patching.',
              'selectors': count, 'script': str(dest), 'script_sha256': sha(dest),
              'helper_sha256': helper_sha256,
              'real_linker': str(linker), 'real_linker_sha256': sha(linker),
              'rustc_host': host, 'rustc_verbose_version': rustc_version,
              'external_wrapper': str(physical_wrapper), 'external_wrapper_sha256': external_wrapper_sha256,
              'link_receipt': str(Path(out) / 'link/linker-invocation.json')}
    env = {'RUSTC_WRAPPER': str(HERE / 'pump_text_layout_rustc.sh'),
           'PUMP_VERIFIED_PYTHON': sys.executable,
           'PUMP_TEXT_ROOT_CRATE': crate_name,
           'PUMP_TEXT_PHYSICAL_WRAPPER': str(physical_wrapper),
           'PUMP_TEXT_LINKER': str(linker), 'PUMP_TEXT_SCRIPT': str(dest),
           'PUMP_TEXT_RECORD_DIR': str(Path(out) / 'link')}
    if certificate_copy:
        env['PUMP_DATA_ORDER_CERTIFICATE'] = str(certificate_copy)
        record['data_order_certificate'] = {'path': str(certificate_copy), 'sha256': sha(certificate_copy)}
    record['environment'] = env
    return env, record


def rustc_command(rustc, args, env):
    # Cargo also asks rustc for its version/target facts without compiling.
    name = args[args.index('--crate-name') + 1] if '--crate-name' in args else None
    kinds = [args[i + 1] for i, value in enumerate(args[:-1]) if value == '--crate-type']
    result = list(args)
    if name == env['PUMP_TEXT_ROOT_CRATE'] and 'cdylib' in kinds:
        result += ['-C', 'linker=' + str(HERE / 'pump_text_layout_linker.sh')]
    return [sys.executable, env['PUMP_TEXT_PHYSICAL_WRAPPER'], rustc, *result]


def reject_attached_script(arg):
    # `-T file` is admitted as two arguments. `-Tfile` is a second script the
    # separate-argument check never sees.
    if isinstance(arg, str) and arg.startswith('-T') and arg != '-T':
        raise AssertionError('attached linker script is not admitted: ' + arg)
    if isinstance(arg, str) and ('-' + arg).startswith(FILE_OPTIONS):
        raise AssertionError('single-dash linker file option is not admitted: ' + arg)
    if isinstance(arg, str) and (
        arg == '--call-graph-ordering-file'
        or arg.startswith('--call-graph-ordering-file=')
    ):
        raise AssertionError('call-graph ordering file is not admitted: ' + arg)


def declared_inputs(args):
    result = {}
    skip = {'-o', '--output', '-L', '--library-path', '--script', '-T', '-z', '-flavor'}
    i = 0
    while i < len(args):
        arg = args[i]
        reject_attached_script(arg)
        if arg in skip:
            check(i + 1 < len(args), 'option missing its argument')
            i += 2
            continue
        check(not arg.startswith('@'), 'response-file input unsupported')
        check(not (arg.startswith('-l') or arg == '--library' or arg.startswith('--library=')), 'library lookup unsupported')
        # These options introduce additional files not present in the admitted
        # SBF recipe. Refuse them rather than leave an unbound file input.
        check(not arg.startswith(('--just-symbols', '--dynamic-list', '--retain-symbols-file',
                                   '--symbol-ordering-file', '--version-script ', '--remap-inputs',
                                   '--export-dynamic-symbol-list')), 'unsupported file option')
        if arg == '--version-script':
            check(i + 1 < len(args), 'option missing its argument')
            result[args[i + 1]] = 'version-script'
            i += 2
            continue
        if arg.startswith('--version-script='):
            result[arg.split('=', 1)[1]] = 'version-script'
        elif not arg.startswith('-') and Path(arg).suffix in SUFFIXES:
            result[arg] = SUFFIXES[Path(arg).suffix]
        elif not arg.startswith('-') and Path(arg).is_file():
            raise AssertionError('unclassified file input: ' + arg)
        i += 1
    return result


def check_bindings(args, records):
    check(declared_inputs(args).keys() == records.keys(), 'input set differs')
    for path, kind in declared_inputs(args).items():
        rec = records[path]
        check(kind == rec['kind'], 'input kind differs')
        data = Path(rec['copy']).read_bytes()
        check(len(data) == rec['bytes'] and hashlib.sha256(data).hexdigest() == rec['sha256'], path)


def prepare_link(args, env):
    directory = Path(env['PUMP_TEXT_RECORD_DIR'])
    directory.mkdir(parents=True, exist_ok=True)
    default = (HERE / 'pump_text_layout_default.ld').read_text()
    replacement = Path(env['PUMP_TEXT_SCRIPT'])
    certificate_path = env.get('PUMP_DATA_ORDER_CERTIFICATE')
    check_script(default, replacement.read_text(), certificate_path)
    records = {}
    for index, (path, kind) in enumerate(declared_inputs(args).items()):
        data = Path(path).read_bytes()
        dest = directory / 'inputs' / f'{index:04d}' / Path(path).name
        dest.parent.mkdir(parents=True)
        dest.write_bytes(data)
        records[path] = {'kind': kind, 'copy': str(dest), 'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest()}
    after, scripts = [], 0
    i = 0
    while i < len(args):
        arg = args[i]
        reject_attached_script(arg)
        if arg in ('--script', '-T'):
            check(Path(args[i + 1]).read_text() == default, 'unexpected SDK script')
            after += [arg, str(replacement)]
            scripts += 1
            i += 2
            continue
        if arg.startswith('--script='):
            check(Path(arg.split('=', 1)[1]).read_text() == default, 'unexpected SDK script')
            arg = '--script=' + str(replacement)
            scripts += 1
        elif arg.startswith('--version-script='):
            arg = '--version-script=' + records[arg.split('=', 1)[1]]['copy']
        elif arg in records:
            arg = records[arg]['copy']
        after.append(arg)
        i += 1
    check(scripts == 1, 'exactly one linker script must be forwarded')
    after.append('-Map=' + str(directory / 'link.map'))
    check_bindings(args, records)
    if certificate_path:
        import pump_data_order
        pump_data_order.check_link(args, records, pump_data_order.load_certificate(certificate_path))
    record = {'input_binding_version': 1, 'incoming': args, 'forwarded': after,
              'link_inputs': records, 'real_linker': env['PUMP_TEXT_LINKER'],
              'real_linker_sha256': sha(env['PUMP_TEXT_LINKER']),
              'replacement_script_sha256': sha(replacement)}
    (directory / 'linker-invocation.json').write_text(json.dumps(record, indent=2) + '\n',encoding='utf-8',newline='\n')
    return [env['PUMP_TEXT_LINKER'], *after]


def finish(record):
    certificate = record.get('data_order_certificate')
    if certificate:
        check(sha(certificate['path']) == certificate['sha256'], 'data-order certificate hash mismatch')
        import pump_data_order
        cert = pump_data_order.load_certificate(certificate['path'])
        pump_data_order.check_combined(Path(record['script']).read_text(), cert)
    check(sha(record['script']) == record['script_sha256'], 'link script hash mismatch')
    check(sha(record['real_linker']) == record['real_linker_sha256'], 'real linker hash mismatch')
    check(sha(record['external_wrapper']) == record['external_wrapper_sha256'], 'external wrapper hash mismatch')
    check(record['helper_sha256'], 'helper hash binding is empty')
    check(all(sha(path) == digest for path, digest in record['helper_sha256'].items()), 'helper hash mismatch')
    inv = json.loads(Path(record['link_receipt']).read_text())
    check_bindings(inv['incoming'], inv['link_inputs'])
    if certificate:
        pump_data_order.check_link(inv['incoming'], inv['link_inputs'], cert)
    check(inv['replacement_script_sha256'] == record['script_sha256'], 'replacement script hash mismatch')
    check(inv['real_linker_sha256'] == record['real_linker_sha256'], 'receipt linker hash mismatch')
    # Verify the actual forwarded file operands point at the bound copies.
    expected = {rec['copy'] for rec in inv['link_inputs'].values()}
    check(set(declared_inputs(inv['forwarded'])) == expected, 'forwarded operands must point at bound copies')
    return dict(record, linker_invocation_sha256=sha(record['link_receipt']),
                bound_inputs=len(inv['link_inputs']))
