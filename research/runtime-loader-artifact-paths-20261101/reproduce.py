"""Actual captured-loader +93-case admin CLI; candidate copies are private."""
from pathlib import Path
import argparse, tempfile, shutil, subprocess, sys, json, hashlib
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();repo=a.repo.resolve();rows=[]
for mode in ['independent','candidate','report']:
 with tempfile.TemporaryDirectory(prefix='loader-receipt-artifacts-') as td:
  temp=Path(td);candidate=temp/'candidate.so';shutil.copyfile(repo/'evidence/original/pump/deployed.so',candidate);report=temp/'report.json';receipt=temp/'loader.json' if mode=='independent' else candidate if mode=='candidate' else report
  before=hashlib.sha256(candidate.read_bytes()).hexdigest()
  cmd=[sys.executable,'-B',str(repo/'scripts/pump_with_captured_loader.py'),'--receipt',str(receipt),str(repo/'scripts/pump_validate_admin.py'),'--candidate',str(candidate),'--output',str(report)]
  result=subprocess.run(cmd,cwd=repo,capture_output=True,text=True,timeout=180)
  data=json.loads(report.read_bytes()) if report.exists() else {};rec=json.loads(receipt.read_bytes()) if receipt.exists() and receipt.read_bytes()[:1]==b'{' else {}
  rows.append({'mode':mode,'returncode':result.returncode,'candidate_changed':before!=hashlib.sha256(candidate.read_bytes()).hexdigest(),'report_case_count':data.get('case_count'),'report_is_loader_receipt':'loads' in data,'loader_ok':rec.get('ok'),'stdout':result.stdout[-1000:],'stderr':result.stderr[-1000:]})
  print(rows[-1],flush=True)
a.output.write_text(json.dumps({'base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'rows':rows},indent=2)+'\n')
