import json,pathlib,subprocess,sys,tempfile
repo=pathlib.Path(sys.argv[1]).resolve();sys.path.insert(0,str(repo/'reconstruction/harness'))
import experiment_runner as e
with tempfile.TemporaryDirectory(prefix='experiment-mode-proof-') as directory:
 root=pathlib.Path(directory);source=root/'source';source.mkdir()
 helper=source/'helper.sh';helper.write_text('#!/bin/sh\nexit 0\n');helper.chmod(0o700)
 command=[sys.executable,'-c','import pathlib,subprocess,sys; subprocess.run([str(pathlib.Path(sys.argv[1])/"helper.sh")],check=True)','{source}']
 first=e.run_trial(source,command,root/'cached')
 helper.chmod(0o601)
 cached=e.run_trial(source,command,root/'cached')
 fresh=e.run_trial(source,command,root/'fresh')
 helper.chmod(0o700)
 output_command=[sys.executable,'-c','import pathlib,sys; p=pathlib.Path(sys.argv[1])/"run.sh"; p.write_text("#!/bin/sh\\nexit 0\\n"); p.chmod(0o700)','{out}']
 initial_output=e.run_trial(source,output_command,root/'output-cache')
 artifact=root/'output-cache'/initial_output['attempt']/'output/run.sh';artifact.chmod(0o601)
 try: subprocess.run([str(artifact)],check=True,capture_output=True);runnable=True
 except PermissionError:runnable=False
 reused_output=e.run_trial(source,output_command,root/'output-cache')
 def summary(r):return {k:r[k] for k in ('status','reused','key','reason')}
 print(json.dumps({'source':{'initial':summary(first),'cached_after_chmod':summary(cached),'fresh_after_chmod':summary(fresh)},'output':{'initial':summary(initial_output),'runnable_after_chmod':runnable,'cached_after_chmod':summary(reused_output)}},indent=2))
