#!/usr/bin/env python3
"""Check saved partial-build provenance against current sources, artifacts and captures."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse,base64,gzip,hashlib,json,pathlib,subprocess,sys
from compare import compare
ROOT=pathlib.Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser();parser.add_argument('--program',choices=['pump','pump_amm','pump_fees','mayhem']);args=parser.parse_args()
for name,status in json.loads((ROOT/'repro/status.json').read_text()).items():
 if args.program and name!=args.program:continue
 if not status.get('candidate_artifact'):continue
 if name=='pump_fees' and status['candidate_artifact']=='research/all-contract-completion-20261028/fees-built/canonical-01/candidate.so':
  subprocess.run([sys.executable,'-B',str(ROOT/'scripts/verify_current_checkpoint.py'),'pump_fees'],check=True)
  continue
 if name=='mayhem' and status['candidate_artifact']=='research/mayhem-canonical-promotion-20261028/hosted/40770208958/candidate.so':
  subprocess.run([sys.executable,'-B',str(ROOT/'scripts/verify_mayhem_checkpoint.py')],check=True)
  continue
 if name=='mayhem' and status['candidate_artifact']=='repro/mayhem/initializer-current-20261027/candidate.so':
  subprocess.run([sys.executable,'-B',str(ROOT/'repro/mayhem/initializer-current-20261027/verify.py'),'--current-source',str(ROOT),'--expected-seal','b6b01b400fb7c5ab10db803ba27fe6a76e0e59e9ea7fad25250dc95760cf485c'],check=True)
  continue
 if name=='pump_amm' and status['candidate_artifact'] in ['repro/pump_amm/v2-mint-clone-recovery-20261028/results/build/candidate.so','repro/pump_amm/canonical-frontier-20261028/results/build-a/candidate.so','research/amm-layout-closure-20261028/results/build-a/candidate.so']:
  subprocess.run([sys.executable,'-B',str(ROOT/'scripts/verify_pump_amm_checkpoint.py')],check=True)
  continue
 if name=='pump' and status['candidate_artifact'] in ['repro/pump/main-contract-round47-20261027/candidate.so','repro/pump/canonical-frontier-20261028/candidate.so','research/pump-create-used-boundaries-20261028/artifacts/candidate.so', 'research/pump-final-composition-673-20261028/artifacts/candidate.so', 'research/pump-multihop-accrual-qualification-20261028/artifacts/candidate.so', 'research/pump-program-creator-notice-qualification-20261028/artifacts/candidate.so']:
  subprocess.run([sys.executable,'-B',str(ROOT/'scripts/verify_pump_main_checkpoint.py')],check=True)
  continue
 if name=='mayhem' and status['candidate_artifact']=='repro/mayhem/compiler-v154-main/main/candidate.so':
  checkpoint=ROOT/'repro/mayhem/compiler-v154-main'
  known='f5d514664d47a04cc22282fdd19ca9e01d835c8a335aa9acc3f637fc61650acc'
  assert sha(checkpoint/'manifest.json')==known
  subprocess.run([sys.executable,'-B',str(checkpoint/'current_bridge.py'),'--current-root',str(ROOT),'--expected-seal',known],check=True)
  print(name,': genuine directv1.54 main;9595 saved comparisons; original whole-file identity false; historical compiler unresolved')
  continue
 manifest=ROOT/status['comparison_report'];report=json.loads(manifest.read_text())
 for source,digest in report['source_sha256'].items():assert sha(ROOT/source)==digest,source
 candidate=ROOT/status['candidate_artifact'];original=ROOT/'evidence/original'/name/'deployed.so'
 assert compare(original.read_bytes(),candidate.read_bytes())==report['comparison'],name
 log_path=ROOT/status['build_log'];log=log_path.read_bytes()
 if log_path.suffix=='.gz':log=gzip.decompress(log)
 assert hashlib.sha256(log).hexdigest()==report['build_log_sha256'],name
 if name=='pump' and status['candidate_artifact']=='repro/pump/remaining-guards-main-fortyeight/main/candidate.so':
  subprocess.run([sys.executable,'-B',str(ROOT/'scripts/verify_pump_remaining_checkpoint.py')],check=True)
  print(name,': remaining-guard checkpoint;9269 saved differential cases and1024 Surfpool comparisons; full original byte equality',report['comparison']['full_byte_equality'])
  continue
 if name=='pump' and status['candidate_artifact']=='repro/pump/admin-cto-compared-errors-main-fortyeight/main/candidate.so':
  subprocess.run([sys.executable,'-B',str(ROOT/'scripts/verify_pump_compared_checkpoint.py')],check=True)
  print(name,': exact compared-error checkpoint;9269 saved differential cases and1024 Surfpool comparisons; full original byte equality',report['comparison']['full_byte_equality'])
  continue
 if name=='pump' and status['candidate_artifact']in['repro/pump/admin-cto-error-batch-main-fortyeight/main/candidate.so','repro/pump/admin-cto-owned-main-fortyeight/main/candidate.so','repro/pump/admin-cto-owned6083-main-fortyeight/main/candidate.so']:
  assert status['validated_cases']==9269
  current=status['candidate_artifact'].removesuffix('/main/candidate.so')
  scratch=ROOT/current.replace('-main-fortyeight','-fortyeight')/'verify.py'
  # This exact artifact has heterogeneous historical receipt schemas. Its bound
  # companion checks all68 receipt hashes/source maps; scratch checks signatures
  # and effects in their original schemas rather than assuming a generic shape.
  subprocess.run([sys.executable,'-B',str(ROOT/'scripts/verify_current_checkpoint.py'),'pump'],check=True)
  subprocess.run([sys.executable,'-B',str(scratch)],check=True)
  print(name,': partial build provenance consistent;9269 saved differential cases and1024 Surfpool comparisons; full byte equality',report['comparison']['full_byte_equality'])
  continue
 if name=='pump_fees' and status['candidate_artifact']=='repro/pump_fees/sharing-authorize-main-v144/main/candidate.so':
  assert status['validated_cases']==17461
  subprocess.run([sys.executable,'-B',str(ROOT/'scripts/verify_current_checkpoint.py'),'pump_fees'],check=True)
  subprocess.run([sys.executable,'-B',str(ROOT/'repro/pump_fees/sharing-authorize-v144/verify.py'),'--runtime-signatures'],check=True)
  print(name,': bound authorization checkpoint;17461 saved comparisons and10 separate sequence steps; full byte equality',report['comparison']['full_byte_equality'])
  continue
 total=0
 seen_receipts=set()
 for receipt_name in status.get('validation_reports',[status.get('validation_report')]):
  assert receipt_name not in seen_receipts,name
  seen_receipts.add(receipt_name)
  receipt=ROOT/receipt_name;data=receipt.read_bytes()
  r=json.loads(gzip.decompress(data) if data.startswith(b'\x1f\x8b') else data)
  assert r['candidate_sha256']==sha(candidate),name
  assert r['original_sha256']==sha(original),name
  assert not r.get('mismatches',[]) and not r.get('failures',[]),name
  assert type(r['case_count']) is int,name
  total+=r['case_count']
 assert type(status['validated_cases']) is int and total==status['validated_cases'],name
 for receipt_name in status.get('signed_sequence_reports',[]):
  receipt=ROOT/receipt_name;data=receipt.read_bytes()
  r=json.loads(gzip.decompress(data) if data.startswith(b'\x1f\x8b') else data)
  assert r['candidate_sha256']==sha(candidate),name
  assert r['original_sha256']==sha(original),name
  assert not r['mismatches'] and not r.get('unexpected_errors',[]) and not r.get('unexpected_original_errors',[]),name
  if 'steps' in r:
   # A receipt that lists no step verifies nothing, and all([]) would accept it.
   assert r['steps'],name
   assert all(step['match'] and step['original']['signature_verification'] and step['candidate']['signature_verification'] for step in r['steps']),name
  if 'signed_transactions' in r:
   assert r['signed_transactions']==len(r['original'])+len(r['candidate'])==2*r['cases'],name
 for evidence in status.get('authentic_historical_replays',[]):
  from solders.transaction import VersionedTransaction
  receipt=ROOT/evidence['report'];data=receipt.read_bytes()
  r=json.loads(gzip.decompress(data) if data.startswith(b'\x1f\x8b') else data)
  assert r['candidate_sha256']==sha(candidate) and r['original_sha256']==sha(original),name
  assert not r['mismatches'] and r['signed_transactions']==2*r['case_count']==2*len(r['cases']),name
  assert 'BlockhashNotFound' in r['freshness_control']['error'],name
  for row in r['cases']:
   capture=json.loads((ROOT/evidence['transactions']/f"admin-success-{row['index']}.json").read_text())['response']['result']
   raw=base64.b64decode(capture['transaction'][0]);tx=VersionedTransaction.from_bytes(raw)
   assert (tx.signatures and all(tx.verify_with_results())) and bytes(tx)==raw,name
   assert row['match'],name
   for side in ['original','candidate']:
    case=row[side]
    assert case['error'] is None and case['signature_verification'] and case['sigverify_runtime_enabled'],name
    assert case['signed_message_and_signature_unchanged'] and not case['blockhash_freshness_check'],name
    assert case['raw_transaction_sha256']==hashlib.sha256(raw).hexdigest(),name
    assert case['signature']==str(tx.signatures[0]) and case['raw_transaction_bytes']==len(raw),name
    assert case['state_matches_static_prediction'] and case['events_match_recorded_history'],name
    assert case['postbalances']==capture['meta']['postBalances'],name
 print(name,': partial build provenance consistent;',total,'saved differential cases; full byte equality',report['comparison']['full_byte_equality'])
