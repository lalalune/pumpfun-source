from pathlib import Path
import json,hashlib,shutil,difflib,subprocess
P=Path('/mnt/c/Users/ahi20/Documents/ChatGPT/pumpfun-contribution-review');B=P/'pump-multihop-clock-20261029';L=Path('/home/ahi200/pumpfun-work/20261029-pump-legacy-exact-sol');label='multihop-current1110-control';parent=L/'source-costs-parent';target=L/('source-'+label)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def inv(p):return {q.relative_to(p).as_posix():sha(q) for q in sorted(p.rglob('*')) if q.is_file()}
expected=json.loads((P/'pump-v3-costs-20261029/delivery/source-parent.json').read_text());before=inv(parent);assert before==expected;assert not target.exists();assert not (L/label).exists();shutil.copytree(parent,target)
source_map=json.loads((B/'current-input-map.json').read_text());changed=[];patch=[]
for item in source_map['changed']:
 name=item['path']
 if not name.endswith('.rs'):continue
 inp=B/'current-source'/name;assert sha(inp)==item['main_sha256'];dest=target/name;old=dest.read_text();new=inp.read_text();shutil.copyfile(inp,dest);changed.append(name);patch.extend(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
assert len(changed)==4;after=inv(target);assert sorted(n for n in before if before[n]!=after[n])==sorted(changed);assert inv(parent)==before
(B/'control-source.patch').write_text(''.join(patch));(B/'control-inputs.json').write_text(json.dumps({'label':label,'current_main':source_map['main'],'selected_parent':'D037','parent_inputs':before,'control_inputs':after,'changed_rust':changed,'excluded_current_workspace_files':[x['path'] for x in source_map['changed'] if not x['path'].endswith('.rs')],'parent_unchanged':True},indent=2)+'\n')
print('PREPARED',label,changed,flush=True);subprocess.run(['python3',str(P/'pump-legacy-exact-sol-20261029/local_build.py'),label],check=True)
