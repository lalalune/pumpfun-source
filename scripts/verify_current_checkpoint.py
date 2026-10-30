#!/usr/bin/env python3
"""Check immutable checkpoint evidence and actual current sources/helper provenance."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINTS = {
    'repro/pump_fees/sharing-authorize-main-v144': ('4049a50a07bfb8a4c51b95776607e86abc3ca1588a8d29f7dfde769a5ed51135', 'helpers', None),
    'repro/pump/admin-cto-error-batch-main-fortyeight': ('4cd1fa3085fd7602d70acbd40e130e33a2232e53771086aff14201b5e7f18890', 'main/build-helpers', 'main/README.final.md'),
    'repro/pump_fees/sharing-fourth-cpi-main-v144': ('b68d33f0d133b1f1283dfa2ce833e2f9c1f398c6c7b16fd177fa91ab74deacfd', 'helpers', None),
    'repro/pump/admin-cto-owned6083-main-fortyeight': ('a994e09c2a8f418fc11f08014542b932333167783224db1f83659fdd62e39e39', 'main/build-helpers', 'main/README.final.md'),
    'repro/pump/admin-cto-owned-main-fortyeight': ('d2e32871cf1a734e05d5e52f30d0b187df97f27061e0d6e1719d2c9f2124778f', 'main/build-helpers', 'main/README.final.md'),
    'repro/pump_amm/init-logical-module-main-v144': ('b420fbb329c8204a130b7bc41fa4db6ac9612f4008836a8961ee95a3ef91cf14', 'main/helpers', 'main/README.final.md'),
    'repro/pump_fees/sharing-second-pump-cpi-main-v144': ('8377e097b9f6d06bf45f3261237f9e6f3513b9ff0f2581c4bc045b4dd91229c3', 'helpers', None),
}
TRANSITION = 'repro/layered-passes/pass-21/build-helper-transition'
TRANSITION_SEAL = 'eb9173e77c85d1b5e55c8556b52e002ad655e5abe3b8a430a13e5a7fe7cb3223'
OLD_HELPER = 'bb683621ffc4297c58f030cb03da54484b7370b786fd8eda965a37f4b3198ee9'
NEW_HELPER = 'e0eccab6f54fee2996039beb53075d9a7b3f411706a90634a44420dec7b173c1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())


def manifest_name(name):
    relative = Path(name)
    if relative.is_absolute() or not relative.parts or '..' in relative.parts:
        raise AssertionError(('Manifest path', name))
    return relative


def _redirected(path):
    """True when path is a symlink or any other reparse point.

    Path.is_symlink() is false for an NTFS directory junction, and Windows has
    no O_NOFOLLOW. lstat exposes the junction as st_reparse_tag 0xA0000003.
    os.path.isjunction is the same fact on Python 3.12 and later.
    """
    try:
        info = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_reparse_tag', 0) != 0:
        return True
    isjunction = getattr(os.path, 'isjunction', None)
    return bool(isjunction and isjunction(path))


def read_regular(bound, path):
    """Read one regular file inside bound without following a redirected directory.

    The walk includes the file, each ancestor, and the bound itself. A symlink
    or a Windows reparse point such as an NTFS junction on any of those
    components is rejected. A hard link to a regular file is still that file
    and is accepted. Hash equality alone must not admit a directory that was
    replaced by a link to another tree.
    """
    bound = Path(os.path.abspath(bound))
    path = Path(os.path.abspath(path))
    try:
        path.relative_to(bound)
    except ValueError:
        raise AssertionError(('Path outside bound', str(path)))
    current = path
    while True:
        if _redirected(current):
            raise AssertionError(('Symlink ancestry', str(current)))
        if current == bound:
            break
        parent = current.parent
        if parent == current:
            raise AssertionError(('Path outside bound', str(path)))
        current = parent
    # Reject a FIFO, socket or device before opening it: a blocking open of a
    # FIFO with no writer never returns. The nonblocking open below keeps a
    # file swapped for a FIFO after this check from blocking as well; the
    # descriptor checks then reject it.
    try:
        listed = os.lstat(path)
    except OSError as error:
        raise AssertionError(('Unreadable path', str(path), error.errno)) from error
    if not stat.S_ISREG(listed.st_mode):
        raise AssertionError(('Nonregular path', str(path)))
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0)
    try:
        fd = os.open(path, flags)
    except OSError as error:
        raise AssertionError(('Unreadable path', str(path), error.errno)) from error
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise AssertionError(('Nonregular path', str(path)))
        data = stream.read()
        after = os.fstat(stream.fileno())
    identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
    current_stat = os.stat(path, follow_symlinks=False)
    if (not stat.S_ISREG(current_stat.st_mode)
            or identity(listed) != identity(before)
            or identity(current_stat) != identity(before)
            or identity(before) != identity(after)):
        raise AssertionError(('Path changed during read', str(path)))
    return data


def file_sha(bound, path):
    return hashlib.sha256(read_regular(bound, path)).hexdigest()


def verify_manifest(package, expected, bound=None):
    package = Path(os.path.abspath(package))
    bound = package if bound is None else Path(os.path.abspath(bound))
    try:
        package.relative_to(bound)
    except ValueError:
        raise AssertionError(('Package outside bound', str(package)))
    raw = read_regular(bound, package / 'manifest.json')
    if hashlib.sha256(raw).hexdigest() != expected:
        raise AssertionError(('Manifest seal', str(package / 'manifest.json')))
    manifest = json.loads(raw)
    files = manifest.get('files', manifest)
    for name, value in files.items():
        data = read_regular(bound, package / manifest_name(name))
        digest = value['sha256'] if isinstance(value, dict) else value
        if hashlib.sha256(data).hexdigest() != digest:
            raise AssertionError(('Manifest mismatch', name))
    return files


def _verify_amm_owner6048(root):
 PUBLIC='repro/pump_amm/owner6048-v144'
 PUBLIC_SEAL='422a6589111b00a2d04e0be10ee52575ef6d1254975cea0b395de0fbdc2851d4'
 READER='5d839d4d7e1c2bf1940722ed5f2e09fc74bba510c5256744732d3770dc0d0edb'
 CANDIDATE='09bee0dfd751dc6ae0240bbac262933c6bda6e0c94aa643f82c57f2956c3a117'
 SYMBOLS='f6e504317ba774325c0ba682e2529c7f18d1ae645a0d7aa239de557729dd0cb4'
 README='83780683ff832dbf418d88a29485a70e83ff6c31797f11829469923882f5098d'
 STATUS='9f4645feb933e8dbdd1867ea72c29fcf3d5d1dbb25873f42cb539e67ecdf721b'
 SOURCE30='0be8e2aea6596710868267de6c7c2375cfb0f0f6ab76df26a9ff15e079a416ce'
 H=sha;J=read
 def safe(root,rel):
  p=Path(rel);assert not p.is_absolute()and'..'not in p.parts;p=root/p
  for q in[p,*p.parents]:
   if q==root.parent:break
   assert not q.is_symlink(),q
  return p
 def saved(command,cwd):
  r=subprocess.run(command,cwd=cwd,capture_output=True);receipt={'command':command,'returncode':r.returncode,'stdout_base64':base64.b64encode(r.stdout).decode('ascii'),'stderr_base64':base64.b64encode(r.stderr).decode('ascii'),'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()}
  if r.returncode:raise RuntimeError('Saved verifier failed: '+json.dumps(receipt))
  return r,receipt
 root=Path(root).absolute();package=safe(root,PUBLIC);assert H(package/'manifest.json')==PUBLIC_SEAL==(package/'manifest.sha256').read_text().split()[0];manifest=J(package/'manifest.json');assert manifest['verify_public.py']==READER and H(package/'verify_public.py')==READER
 status=J(root/'repro/status.json')['pump_amm'];assert hashlib.sha256(json.dumps(status,sort_keys=True,separators=(',',':')).encode()).hexdigest()==STATUS
 assert status==J(package/'selection-proposal/status.proposed.json')['pump_amm'];assert status['candidate_artifact']==PUBLIC+'/main/candidate.so'and status['candidate_sha256']==CANDIDATE
 assert status['comparison_report']==PUBLIC+'/main/build-01/build-comparison.json'and status['main_acceptance_verifier']==PUBLIC+'/verify_public.py'
 assert H(root/'programs/pump-amm/README.md')==README==H(package/'selection-proposal/README.proposed.md')
 assert H(package/'main/candidate.so')==CANDIDATE and H(package/'main/unstripped.so')==SYMBOLS
 sourcefile=package/'managed-plan/witness/proposed-source30.json';assert H(sourcefile)==SOURCE30;source=J(sourcefile);assert len(source)==30
 report=J(package/'main/build-01/build-comparison.json');identity=J(package/'main/identity.json');assert report['source_sha256']==source==identity['actual_managed_source30']and identity['source_overlay_used']is False and identity['whole_candidate_equal']and identity['whole_symbols_equal'];assert report['comparison']['candidate_sha256']==CANDIDATE
 for name,h in source.items():assert H(safe(root,name))==h,name
 # Retain the existing explicit historical helper transition; no new drift rule.
 protected=J(package/'managed-plan/witness/protected-before.json');transitions=[]
 for name,recorded in protected.items():
  if not name.startswith('scripts/'):continue
  actual=H(safe(root,name))
  if actual==recorded:continue
  assert name=='scripts/build_partial_candidate.py'and(recorded,actual)in[(OLD_HELPER,NEW_HELPER),(NEW_HELPER,OLD_HELPER)],name
  proof=safe(root,TRANSITION);assert H(proof/'manifest.json')==TRANSITION_SEAL;rows=J(proof/'manifest.json');rows=rows.get('files',rows)
  for n,v in rows.items():assert H(safe(proof,n))==(v['sha256']if isinstance(v,dict)else v)
  assert H(proof/'before.py')==OLD_HELPER and H(proof/'after.py')==NEW_HELPER
  _,receipt=saved([sys.executable,'-B',str(proof/'verify.py')],proof);transitions.append({'path':name,'recorded_sha256':recorded,'current_sha256':actual,'proof_seal':TRANSITION_SEAL,'receipt':receipt})
 # This exact public command performs all physical/logical/derived-data checks
 # and optional source30 discovery. It never calls old live preflight/HEAD/index.
 r,receipt=saved([sys.executable,'-B',str(package/'verify_public.py'),'--current-main',str(root)],package);observed=json.loads(r.stdout)
 assert observed['schema']=='AMM_PUBLIC_SAVED_CHECKS_V1'and observed['status']=='PASS'and observed['returncode']==0 and observed['verification_mode']=='saved_bytes'and observed['children']==[]
 assert observed['optional_current_source']['source30_bytes_and_inventory_equal']is True and observed['historical_engine_records_checked']is True and observed['live_old_preflight_or_HEAD_index_called']is False
 assert observed['new_target_executions']==observed['new_builds']==observed['compiler_VM_runs']==observed['verified_signatures']==0
 return {'status':'PASS','program':'pump_amm','public_seal':PUBLIC_SEAL,'candidate_sha256':CANDIDATE,'symbols_sha256':SYMBOLS,'source_inputs':30,'actual_current_sources_checked':True,'README_exact':True,'selected_AMM_status_exact':True,'reviewed_helper_transitions':transitions,'saved_public_verifier':receipt,'fresh_signature_verification_performed':False,'target_executions':0,'new_builds':0,'original_global_failure_exits_rewritten':False}


def verify(program, root):
    status = json.loads(read_regular(root, root / 'repro/status.json'))[program]
    if program == 'pump' and status['candidate_artifact'] in ['repro/pump/canonical-frontier-20261028/candidate.so', 'research/pump-create-used-boundaries-20261028/artifacts/candidate.so', 'research/pump-final-composition-673-20261028/artifacts/candidate.so', 'research/pump-multihop-accrual-qualification-20261028/artifacts/candidate.so', 'research/pump-program-creator-notice-qualification-20261028/artifacts/candidate.so']:
        from verify_pump_main_checkpoint import verify as verify_pump
        return verify_pump(root)
    if program == 'pump_amm' and status['candidate_artifact'] in ['repro/pump_amm/canonical-frontier-20261028/results/build-a/candidate.so', 'research/amm-layout-closure-20261028/results/build-a/candidate.so']:
        from verify_pump_amm_checkpoint import verify as verify_amm
        return verify_amm(root)
    if program == 'mayhem' and status['candidate_artifact'] == 'research/mayhem-canonical-promotion-20261028/hosted/40770208958/candidate.so':
        from verify_mayhem_checkpoint import verify as verify_mayhem
        return verify_mayhem(root)
    if program == 'pump_fees' and status['candidate_artifact'] == 'research/all-contract-completion-20261028/fees-built/canonical-01/candidate.so':
        def require(value, message):
            if not value:
                raise ValueError(message)
        packet = root / 'research/all-contract-completion-20261028'
        require(sha(packet / 'fees-selection.json') == status['source_identity_report_sha256'], 'Fees selection binding')
        result = subprocess.run([sys.executable, '-B', str(root / 'research/all-contract-completion-20261028/verify_current_fees.py'), '--repo', str(root)], capture_output=True, text=True, check=True)
        detail = json.loads(result.stdout)
        require(detail['meaningful_elf_equal'] is True and detail['meaningful_elf_bytes'] == 873256, 'Fees meaningful ELF identity')
        require(detail['candidate_sha256'] == status['candidate_sha256'], 'Fees selected candidate hash')
        require(detail['symbols_sha256'] == status['symbols_sha256'], 'Fees selected symbols hash')
        require(sha(root / status['candidate_artifact']) == detail['candidate_sha256'], 'Fees literal candidate binding')
        require(sha(root / status['candidate_symbols_artifact']) == detail['symbols_sha256'], 'Fees literal symbols binding')
        require(sha(root / 'Cargo.toml') == status['workspace_manifest_sha256'], 'Fees workspace manifest binding')
        require(sha(root / 'Cargo.lock') == status['workspace_lock_sha256'], 'Fees workspace lock binding')
        runtime = subprocess.run([sys.executable, '-B', str(root / 'research/contract-completion-20261028/verify_fees_runtime.py'), '--repo', str(root)], capture_output=True, text=True, check=True)
        detail['fresh_runtime_qualification'] = json.loads(runtime.stdout)
        return {'status': 'PASS', 'program': program, 'candidate_sha256': detail['candidate_sha256'], 'actual_current_sources_checked': True, 'meaningful_elf_equal': True, 'source_and_build': detail}
    if program == 'pump_amm' and status['candidate_artifact'] == 'repro/pump_amm/v2-mint-clone-recovery-20261028/results/build/candidate.so':
        from verify_pump_amm_checkpoint import verify as verify_amm
        return verify_amm(root)
    if program == 'pump' and status['candidate_artifact'] == 'repro/pump/main-contract-round47-20261027/candidate.so':
        from verify_pump_main_checkpoint import verify as verify_main
        return verify_main(root)
    suffix = '/main/candidate.so'
    assert status['candidate_artifact'].endswith(suffix)
    name = status['candidate_artifact'][:-len(suffix)]
    if program == 'pump_amm' and name == 'repro/pump_amm/owner6048-v144':
        return _verify_amm_owner6048(root)
    if program == 'pump' and name == 'repro/pump/remaining-guards-main-fortyeight':
        from verify_pump_remaining_checkpoint import verify as verify_remaining
        return verify_remaining(root)
    if program == 'pump' and name == 'repro/pump/admin-cto-compared-errors-main-fortyeight':
        from verify_pump_compared_checkpoint import verify as verify_compared
        return verify_compared(root)
    assert name in CHECKPOINTS, ('Checkpoint needs explicit bridge review', name)
    seal, helper_prefix, final_readme = CHECKPOINTS[name]
    package = root / name
    verify_manifest(package, seal, root)
    scratch_bindings = {
        'repro/pump_fees/sharing-authorize-main-v144': ('repro/pump_fees/sharing-authorize-v144', '52cd978029f67b8c79e738131fa2bec3251de8fdfc2a22270e1464b210125ba7'),
        'repro/pump/admin-cto-error-batch-main-fortyeight': ('repro/pump/admin-cto-error-batch-fortyeight', 'd9d6adc2f5d1533c04999626f93d1aef6a6d0acfb100a11483b4ca777ef62cd6'),
        'repro/pump_fees/sharing-fourth-cpi-main-v144': ('repro/pump_fees/sharing-fourth-cpi-v144', 'e21ebdbc98cf49cb391697ae0b50699814107d292caab68a83c22a3265641fd4'),
    }
    if name in scratch_bindings:
        scratch, scratch_seal = scratch_bindings[name]
        verify_manifest(root / scratch, scratch_seal, root)
    report = json.loads(read_regular(root, root / status['comparison_report']))
    assert root / status['comparison_report'] == package / 'main/build-comparison.json'
    assert report['selected_toolchain'] in ('v1.44', 'v1.52')
    command = report['command']
    assert command[command.index('--tools-version') + 1] == report['selected_toolchain']
    candidate_sha = file_sha(root, root / status['candidate_artifact'])
    if candidate_sha != report['comparison']['candidate_sha256'] or candidate_sha != status['candidate_sha256']:
        raise AssertionError(status['candidate_artifact'])
    for source, expected_digest in report['source_sha256'].items():
        if file_sha(root, root / source) != expected_digest:
            raise AssertionError(source)
    if final_readme:
        crate = 'pump' if program == 'pump' else 'pump-amm'
        if read_regular(root, root / 'programs' / crate / 'README.md') != read_regular(root, package / final_readme):
            raise AssertionError(final_readme)
    controls_prefix = 'controls' if name == 'repro/pump_fees/sharing-authorize-main-v144' else 'main/controls'
    gate = json.loads(read_regular(root, package / controls_prefix / 'gate-before.json'))
    transitions = []
    for helper, recorded in gate['helpers'].items():
        if file_sha(root, package / helper_prefix / helper) != recorded:
            raise AssertionError(helper)
        actual = file_sha(root, root / helper)
        if actual == recorded:
            continue
        assert helper == 'scripts/build_partial_candidate.py' and (recorded, actual) in ((OLD_HELPER, NEW_HELPER), (NEW_HELPER, OLD_HELPER)), helper
        proof = root / TRANSITION
        verify_manifest(proof, TRANSITION_SEAL, root)
        if file_sha(root, proof / 'before.py') != OLD_HELPER or file_sha(root, proof / 'after.py') != NEW_HELPER:
            raise AssertionError('helper transition bytes')
        # Discard only stdout; a failing proof must report its assertion on stderr.
        subprocess.run([sys.executable, '-B', str(proof / 'verify.py')], check=True, stdout=subprocess.DEVNULL)
        transitions.append({'path': helper, 'recorded_sha256': recorded, 'current_sha256': actual, 'proof_seal': TRANSITION_SEAL})
    # Immutable verifier retains its original helper checks and all source/artifact
    # evidence. Current-source and reviewed-helper checks are performed above.
    # Discard only stdout; a failing verifier must report its assertion on stderr.
    subprocess.run([sys.executable, '-B', str(package / 'verify.py')], check=True, stdout=subprocess.DEVNULL)
    return {'status': 'PASS', 'program': program, 'candidate_sha256': candidate_sha, 'source_inputs': len(report['source_sha256']),
            'actual_current_sources_checked': True, 'reviewed_helper_transitions': transitions,
            'recorded_toolchain': report['selected_toolchain'], 'target_executions': 0, 'original_global_failure_exits_rewritten': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('program', choices=['pump', 'pump_amm', 'pump_fees', 'mayhem'])
    parser.add_argument('--repo', type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.repo.resolve()
    selection = json.loads(read_regular(args.repo, args.repo / 'repro/status.json'))
    if args.program == 'pump' and selection['pump'].get('candidate_artifact') == 'repro/pump/remaining-guards-main-fortyeight/main/candidate.so':
        root = args.repo.absolute()
    if args.program == 'pump' and selection['pump'].get('candidate_artifact') == 'repro/pump/admin-cto-compared-errors-main-fortyeight/main/candidate.so':
        root = args.repo.absolute()
    print(json.dumps(verify(args.program, root), indent=2))
