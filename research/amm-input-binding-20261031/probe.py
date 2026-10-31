"""Real native linker-wrapper outputs versus production attempt admission."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

repo, lld, clang = map(Path, sys.argv[1:4])
repo = repo.resolve(); lld = lld.resolve(); clang = clang.resolve()
sys.path.insert(0, str(repo / 'scripts/amm_sell'))
import try_sell as runner
import native_build

with tempfile.TemporaryDirectory(prefix='amm-link-inputs-') as folder:
    root = Path(folder)
    runner.SWARM = root / 'swarm'
    runner.SOURCES = runner.SWARM / 'sources'; runner.SOURCES.mkdir(parents=True)
    baseline = runner.SWARM / 'baselines/pristine-ws'
    (baseline / native_build.SELL_REL).parent.mkdir(parents=True)
    (baseline / native_build.SELL_REL).write_bytes(b'// unchanged source\n')
    native_build.PRISTINE = baseline
    original = runner.SWARM / 'infra/original/deployed.so'
    original.parent.mkdir(parents=True); original.write_bytes(b'context input')
    (root / 'probe.c').write_text('int probe(void) { return 7; }\n')
    subprocess.run([str(clang), '--target=x86_64-unknown-linux-gnu', '-c', '-ffunction-sections',
                    '-fno-asynchronous-unwind-tables', str(root / 'probe.c'), '-o', str(root / 'probe.o')], check=True)
    (root / 'wrapper.py').write_text(native_build.LINKER_WRAPPER)
    ordered = native_build.native_link_script()
    (root / 'ordered-native.ld').write_bytes(ordered)
    external = root / 'external.ld'
    rows = []
    for case in ('default', 'empty', 'changed-after-admission'):
        external.write_bytes(ordered if case == 'changed-after-admission' else b'')
        supplied = str(external) if case != 'default' else None
        args = SimpleNamespace(lane='fixture', slot='0', sell=None, patch=None,
                               extra_root_flags='', link_script=supplied, disasm=False)
        if hasattr(runner, 'input_snapshot'):
            key_doc, blobs = runner.input_snapshot(baseline, sell=None, patch=None, flags='',
                                                   link_script=supplied, want_disasm=False)
            paths = {name: runner.retain_input(data, {'sell':'.rs','patch':'.patch','link':'.ld'}[name])
                     for name, data in blobs.items() if data is not None}
            selected = str(paths['link']) if supplied else None
        else:
            body = next(n for n in ast.parse(Path(runner.__file__).read_text()).body
                        if isinstance(n, ast.FunctionDef) and n.name == 'main').body
            start = next(i for i,n in enumerate(body) if isinstance(n,ast.Assign)
                         and any(isinstance(t,ast.Name) and t.id=='lane_build' for t in n.targets))
            end = next(i for i,n in enumerate(body) if isinstance(n,ast.Assign)
                       and any(isinstance(t,ast.Name) and t.id=='key' for t in n.targets))
            scope = dict(vars(runner), a=args)
            module = ast.fix_missing_locations(ast.Module(body=body[start:end+1],type_ignores=[]))
            exec(compile(module,str(runner.__file__),'exec'),scope)
            key_doc = scope['key_doc']; selected = supplied
        key = runner.sha(json.dumps(key_doc,sort_keys=True).encode())
        if case == 'changed-after-admission': external.write_bytes(b'')
        out = root / case; out.mkdir()
        env = dict(os.environ, AMM_LANE_OUT=str(out), AMM_LANE_HARNESS=str(root), AMM_LAYOUT_REAL_LLD=str(lld))
        if selected: env['AMM_LINK_SCRIPT'] = selected
        else: env.pop('AMM_LINK_SCRIPT',None)
        result = subprocess.run([sys.executable,str(root/'wrapper.py'),'-flavor','gnu','-shared','--script',
                                 str(repo/'reconstruction/harness/sbf_default.ld'),str(root/'probe.o'),
                                 '-o',str(out/'candidate.so')],env=env,capture_output=True,text=True,timeout=30)
        if result.returncode: raise RuntimeError(result.stderr)
        rows.append({'case':case,'key':key,'admitted_link_sha256':key_doc['link'],
                     'used_link_sha256':hashlib.sha256(Path(selected).read_bytes()).hexdigest() if selected else None,
                     'candidate_sha256':hashlib.sha256((out/'candidate.so').read_bytes()).hexdigest(),
                     'candidate_bytes':(out/'candidate.so').stat().st_size})
    print(json.dumps({'base':'90300f9d2efe3ef014b116172251a41bfb104d78',
                      'linker':subprocess.check_output([str(lld),'-flavor','gnu','--version'],text=True).strip(),
                      'rows':rows},indent=2))
