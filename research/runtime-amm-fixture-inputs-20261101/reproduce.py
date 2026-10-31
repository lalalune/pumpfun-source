"""Run real AMM CLIs using private caller fixtures; never mutate checkout inputs."""
import argparse, hashlib, json, os, pathlib, shutil, subprocess, sys, tempfile
p=argparse.ArgumentParser();p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();repo=a.repo.resolve()
TRADE='research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json'
MIGRATION='research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json'
IDL='evidence/upstream/pump.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
rows=[]
for script,target in [('pump_amm_collect_differential.py',TRADE),('pump_amm_migration_create_differential.py',MIGRATION),('pump_amm_transfer_creator_differential.py',IDL),('pump_amm_boost_differential.py',MIGRATION)]:
 for mode in ['independent-output','fixture-output']:
  with tempfile.TemporaryDirectory(prefix='amm-caller-') as tmp:
   cwd=pathlib.Path(tmp)
   for name in [TRADE,MIGRATION,IDL]:
    path=cwd/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/name,path)
   before={name:sha((cwd/name).read_bytes()) for name in [TRADE,MIGRATION,IDL]}
   output=cwd/target if mode=='fixture-output' else cwd/'report.json'
   completed=subprocess.run([sys.executable,'-B',str(repo/'scripts'/script),'--candidate',str(repo/'evidence/original/pump_amm/deployed.so'),'--output',str(output)],cwd=cwd,capture_output=True,text=True,timeout=240)
   after={name:sha((cwd/name).read_bytes()) for name in before}
   report=None
   if output.exists():
    payload=json.loads(output.read_bytes())
    if 'case_count' in payload: report={'case_count':payload['case_count'],'mismatches':payload['mismatches'],'cases_sha256':sha(json.dumps(payload['cases'],sort_keys=True,separators=(',',':')).encode())}
   row={'script':script,'mode':mode,'target':target,'returncode':completed.returncode,'fixture_changed':[name for name in before if before[name]!=after[name]],'before':before,'after':after,'report':report,'stdout':completed.stdout[-1500:],'stderr':completed.stderr[-2500:]}
   rows.append(row);print(script,mode,completed.returncode,row['fixture_changed'],report and report['case_count'],flush=True)
a.output.write_text(json.dumps({'base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'rows':rows},indent=2)+'\n')
