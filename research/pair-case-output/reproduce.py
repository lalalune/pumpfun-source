"""Real macOS CLI proof of paired-build source preservation; no compiler runs."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O, -OO or PYTHONOPTIMIZE.')
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT/'work/scoped-proof'
sys.path.insert(0,str(ROOT/'reconstruction/harness'))
from source_inputs import snapshot


def run(command,**kwargs):
    return subprocess.run(command,check=True,capture_output=True,**kwargs)


def main():
    transition=json.loads((HERE/'transition.json').read_text())
    harness=ROOT/'reconstruction/harness/build_score_pair.py'
    digest=hashlib.sha256(harness.read_bytes()).hexdigest()
    stage=next((key for key in ('before','after') if transition[key]==digest),None)
    if stage is None:raise RuntimeError('paired-build source is outside the reviewed transition')
    OUT.mkdir(parents=True,exist_ok=False)
    environment={k:v for k,v in os.environ.items() if not k.upper().startswith('GIT_')}
    environment.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_ALLOW_PROTOCOL='file',GIT_NO_LAZY_FETCH='1',PYTHONDONTWRITEBYTECODE='1')
    original=snapshot(ROOT/'programs/pump')
    rows={}
    for label in ('base-case-alias','candidate-case-alias','lexical-control','symlink-control','ancestor-control','disjoint-control'):
        with tempfile.TemporaryDirectory(prefix='pair-case-proof-') as temporary:
            directory=Path(temporary)
            base=directory/'case-base';candidate=directory/'case-candidate'
            def ignore(path,names):
                return ['target'] if Path(path)==ROOT/'programs/pump' and 'target' in names else []
            shutil.copytree(ROOT/'programs/pump',base/'programs/pump',ignore=ignore)
            def git(repo,*arguments):
                return run(['git','-C',str(repo),'-c','user.name=Local Reproduction',
                    '-c','user.email=local-reproduction@example.invalid','-c','commit.gpgsign=false',
                    '-c','core.hooksPath=/dev/null',*arguments],env=environment).stdout
            git(base,'init','-q');git(base,'add','-f','-A');git(base,'commit','-qm','Actual retained Pump source')
            run(['git','clone','--quiet','--no-hardlinks',str(base),str(candidate)],env=environment)
            before={name:snapshot(repo/'programs/pump') for name,repo in (('base',base),('candidate',candidate))}
            assert before['base']==before['candidate']==original, 'copied source differs from the actual selected crate'
            alias_base=directory/'CASE-BASE';alias_candidate=directory/'CASE-CANDIDATE'
            assert alias_base.exists() and alias_base.samefile(base), 'requires a real case-insensitive filesystem'
            assert alias_candidate.exists() and alias_candidate.samefile(candidate)
            if label=='base-case-alias': output=alias_base/'programs/pump/new-evidence'
            elif label=='candidate-case-alias': output=alias_candidate/'programs/pump/new-evidence'
            elif label=='lexical-control': output=base/'programs/pump/new-evidence'
            elif label=='symlink-control':
                alias=directory/'source-link';alias.symlink_to(base,target_is_directory=True)
                output=alias/'programs/pump/new-evidence'
            elif label=='ancestor-control': output=base
            else: output=directory/'separate-output'
            existed=output.exists()
            command=[sys.executable,'-B',str(harness),'--base',str(base),'--candidate',str(candidate),
                     '--out',str(output),'--sdk',str(directory/'missing-sdk'),'--hybrid',str(directory/'missing-hybrid')]
            process=subprocess.run(command,cwd=ROOT,env=environment,capture_output=True,text=True,
                encoding='utf-8',errors='replace',timeout=120)
            after={name:snapshot(repo/'programs/pump') for name,repo in (('base',base),('candidate',candidate))}
            row={'command':command,'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr,
                 'output_existed':existed,'output_exists':output.exists(),
                 'scoring_original_exists':(output/'scoring-inputs/original.so').is_file(),
                 'source_before':before,'source_after':after,
                 'source_unchanged':{name:before[name]==after[name] for name in before},
                 'git_status':{name:git(repo,'status','--porcelain').decode('utf-8','replace')
                               for name,repo in (('base',base),('candidate',candidate))},
                 'real_case_alias_verified':True}
            (OUT/(label+'.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8',newline='\n')
            assert process.returncode==2, row
            overlap='output must not overlap a Pump source tree' in process.stderr
            if label=='disjoint-control':
                assert not overlap and 'missing-hybrid' in process.stderr
                assert row['scoring_original_exists'] and all(row['source_unchanged'].values())
            elif stage=='before' and label.endswith('case-alias'):
                assert not overlap and 'missing-hybrid' in process.stderr
                selected='base' if label.startswith('base') else 'candidate'
                assert row['scoring_original_exists'] and row['source_unchanged'][selected] is False
                assert row['source_unchanged']['candidate' if selected=='base' else 'base'] is True
                old={item['path']:item for item in before[selected]['files']}
                new={item['path']:item for item in after[selected]['files']}
                assert all(new.get(name)==value for name,value in old.items()), 'original source file changed'
            else:
                assert overlap and row['output_exists']==existed and all(row['source_unchanged'].values())
            rows[label]={key:row[key] for key in ('returncode','output_exists','scoring_original_exists','source_unchanged')}
    tests=[]
    for name in ('test_build_pair_source_overlap.py','test_pair_case_alias.py','test_build_pair_boundaries.py',
                 'test_build_score_pair.py','test_build_score_pair_scorer_modules.py'):
        command=[sys.executable,'-B',str(ROOT/'reconstruction/harness'/name)]
        result=subprocess.run(command,cwd=ROOT,env=environment,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        (OUT/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8',newline='\n')
        tests.append({'command':command,'returncode':result.returncode})
        assert result.returncode==0,(name,result.stdout,result.stderr)
    summary={'revision':run(['git','rev-parse','HEAD'],cwd=ROOT,text=True).stdout.strip(),'stage':stage,
        'paired_build_sha256':digest,'original_source':original,'rows':rows,'tests':tests,
        'scope':'Actual source trees and paired-build CLI preflight on a real case-insensitive macOS filesystem; deliberately absent SDK controls. No source compilation, scorer execution, binary-equivalence or runtime result.'}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'stage':stage,'rows':rows,'tests':tests},indent=2))


if __name__=='__main__':main()
