#!/usr/bin/env python3
"""SOURCE-ONLY PROPOSAL: one explicit Linux measurement, never a promotion tool."""
if not __debug__:
 raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
from pathlib import Path,PurePosixPath
import argparse,datetime,gzip,hashlib,importlib.util,json,os,platform,re,shutil,shlex,struct,subprocess,sys,tarfile,tempfile,tomllib,traceback,urllib.request
ASSETS={
 'compiler':{'tag':'v1.48','release_id':218636077,'id':254652416,'name':'platform-tools-linux-x86_64.tar.bz2','size':516334851,'digest':None},
 'strip':{'tag':'v1.52','release_id':258591601,'id':310634197,'name':'platform-tools-linux-x86_64.tar.bz2','size':519270959,'digest':'sha256:8b3861e93daf085ec12b65c4fac374d9bec4587a3de16871da6b08ab0c1d907e'}}
OLD='repro/donation-relay/source-build-12-idl-discriminator-owned'
MAC='repro/donation-relay/source-build-12-v148-measurement'
OLD_SEAL='d12ad064c15a5e1760f6a566349f982b9e4e4e57430b455a0386b89a4a57248a'
MAP_SHA='3b3f75fb4617075552f2d07e02b5dc2a9b53221eb35118f87ed44ac45f74b943'
REGISTRY_SHA='635ef97159e65f2f9098fb561424aa25e37806dc49e71e89bf2b7d46475ff5fc'
METHOD_SHA='095fc2d63be0fe4233bdf4e5946cac8d03d9b1747fd39147eea9a98c12dda175'
ELF_METHOD_SHA='79deec70c7e2751cd5e3733566ca4fcca9666268b2cb056a447118cadb80b4ed'
WINDOWS_SHA='bbe3bb0f5003d457266e0a279c052026306100df316cbd344919cc2da13bc2cc'
MAC_SHA='6c32f830015bc52a890264041c20c74441db651d8f6efd6558d8fa13adec1783'
TARGET_SHA='367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563'
RUST_SHA='293a1b6c60a0b8d92593843c373539e21e3ba087'
H=lambda b:hashlib.sha256(b).hexdigest()
J=lambda p:json.loads(Path(p).read_text())
def write(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def files(root):
 root=Path(root);out={}
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink(),p
  if p.is_file():out[str(p.relative_to(root))]=H(p.read_bytes())
 return out

def source_inputs(repo):
 old=repo/OLD;assert H((old/'manifest.json').read_bytes())==OLD_SEAL
 assert H((old/'launcher/resolved-source-sha256.json').read_bytes())==MAP_SHA
 assert H((old/'launcher/resolved-source-archive-equality.json').read_bytes())==REGISTRY_SHA
 m=J(old/'launcher/resolved-source-sha256.json');assert len(m)==23 and files(old/'source')==m
 profile=tomllib.loads((old/'source/Cargo.toml').read_text())['profile']['release'];assert profile=={'panic':'abort','overflow-checks':True,'lto':False,'codegen-units':1}
 return m

def plan(repo,output):
 repo=Path(repo).resolve();output=Path(output).absolute();m=source_inputs(repo)
 assert not output.exists(),'Choose a fresh measurement output path; existing evidence is never deleted'
 return {'mode':'one future controlled measurement; source-only proposal until explicitly executed','repo':str(repo),'output':str(output),'required_runner':'Ubuntu24.04 x86_64','assets':ASSETS,'frozen_source':m,'registry_map_sha256':REGISTRY_SHA,'profile':{'opt-level':3,'panic':'abort','overflow-checks':True,'lto':False,'codegen-units':1},'target':'sbf-solana-solana','rustflags':'-Zremap-cwd-prefix=','expected_stock_features':'+store-imm,+jmp-ext','network':'official asset acquisition and one cargo fetch --locked preparation only; program build offline','program_build_attempt_limit':1,'os_and_tool_bytes_differ_from_Darwin_control':True,'same_full_recipe_claimed':False,'runtime_or_chain_execution':False,'accepted_or_default_changes':False,'output_created':False}

def selected_asset(release,pin):
 assert release['id']==pin['release_id']
 a=next(x for x in release['assets']if x['id']==pin['id'])
 for k in ['name','size','digest']:assert a.get(k)==pin[k],k
 url='https://github.com/anza-xyz/platform-tools/releases/download/'+pin['tag']+'/'+pin['name'];assert a['browser_download_url']==url
 return a

def fetch_asset(pin,directory):
 directory.mkdir(parents=True,exist_ok=False);url='https://api.github.com/repos/anza-xyz/platform-tools/releases/tags/'+pin['tag']
 release=json.loads(urllib.request.urlopen(url,timeout=120).read());write(directory/'release.json',release);a=selected_asset(release,pin)
 archive=directory/pin['name'];digest=hashlib.sha256();count=0;failure=None
 try:
  with urllib.request.urlopen(a['browser_download_url'],timeout=180)as src,archive.open('xb')as dst:
   while chunk:=src.read(1024*1024):dst.write(chunk);digest.update(chunk);count+=len(chunk)
 except Exception as error:failure=error
 measured=digest.hexdigest();size_ok=count==pin['size'];hash_ok=pin['digest']is None or pin['digest']=='sha256:'+measured
 status='DOWNLOAD_FAILED'if failure else'SIZE_MISMATCH'if not size_ok else'DIGEST_MISMATCH'if not hash_ok else'ACQUIRED'
 # Record observed evidence before either validation assertion can terminate setup.
 receipt={'pin':pin,'official_url':a['browser_download_url'],'archive_path':str(archive),'bytes':count,'expected_bytes':pin['size'],'measured_sha256':measured,'expected_publisher_digest':pin['digest'],'size_match':size_ok,'digest_match_or_unavailable':hash_ok,'status':status,'publisher_digest_available':pin['digest']is not None,'publisher_digest_verified':pin['digest']is not None and hash_ok,'provenance_limit':'v148 has no publisher digest; official-origin acquisition plus measured archive/member seal only','time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 if failure:receipt['download_error']=type(failure).__name__+': '+str(failure)
 write(directory/'acquisition.json',receipt)
 if failure:raise failure
 assert size_ok,'Official asset size mismatch; measured acquisition receipt retained'
 assert hash_ok,'Official publisher digest mismatch; measured acquisition receipt retained'
 return archive

def extract_verified(archive,destination):
 destination.mkdir(parents=True,exist_ok=False);members={};seen=set()
 with tarfile.open(archive,'r|bz2')as tf:
  for m in tf:
   name=m.name.removeprefix('./');part=PurePosixPath(name);assert not part.is_absolute()and'..'not in part.parts and name not in seen;seen.add(name)
   if not m.isfile():tf.extract(m,destination,filter='data');continue
   target=destination/name;target.parent.mkdir(parents=True,exist_ok=True);assert target.resolve().is_relative_to(destination.resolve())
   digest=hashlib.sha256()
   with tf.extractfile(m)as src,target.open('xb')as dst:
    while chunk:=src.read(1024*1024):dst.write(chunk);digest.update(chunk)
   target.chmod(m.mode);assert target.stat().st_size==m.size
   members[name]={'sha256':digest.hexdigest(),'bytes':m.size}
 return members

def member(root,path,members):
 f=root/path;real=str(f.resolve().relative_to(root.resolve()));assert real in members;assert H(f.read_bytes())==members[real]['sha256'];return {'path':path,'archive_member':real,**members[real]}

def tools(root,members):
 chosen={}
 for name in ['rust/bin/rustc','rust/bin/cargo','rust/bin/rustdoc','llvm/bin/clang','llvm/bin/llvm-ar','llvm/bin/llvm-objdump','llvm/bin/llvm-objcopy']:chosen[name]=member(root,name,members)
 for path in members:
  if path.startswith('rust/lib/')and('/sbf-solana-solana/lib/'in path or '/sbpf-solana-solana/lib/'in path or path.endswith('/bin/rust-lld')or'.so'in Path(path).name):chosen[path]=member(root,path,members)
 assert RUST_SHA in(root/'version.md').read_text();chosen['version.md']=member(root,'version.md',members)
 return chosen

def environment(compiler,work):
 return {'PATH':os.pathsep.join([str(compiler/'rust/bin'),str(compiler/'llvm/bin'),'/usr/bin','/bin']),'CARGO_HOME':str(work/'cargo-home'),'CARGO_TARGET_DIR':str(work/'target'),'RUSTUP_HOME':str(work/'rustup'),'CARGO_NET_OFFLINE':'false','CARGO_TERM_COLOR':'never','RUSTC':str(compiler/'rust/bin/rustc'),'RUSTDOC':str(compiler/'rust/bin/rustdoc'),'CARGO_TARGET_SBF_SOLANA_SOLANA_RUSTFLAGS':'-Zremap-cwd-prefix=','CC':str(compiler/'llvm/bin/clang'),'AR':str(compiler/'llvm/bin/llvm-ar'),'OBJDUMP':str(compiler/'llvm/bin/llvm-objdump'),'OBJCOPY':str(compiler/'llvm/bin/llvm-objcopy'),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}

def run_once(label,command,env,cwd,receipts):
 receipts.mkdir(parents=True,exist_ok=True);log=receipts/(label+'.log');record=receipts/(label+'.json')
 with record.open('x')as f:json.dump({'command':command,'state':'started'},f)
 row={'command':command,'cwd':str(cwd),'environment':env}
 try:
  with log.open('xb')as output:r=subprocess.run(command,cwd=cwd,env=env,stdout=output,stderr=subprocess.STDOUT)
  row.update(returncode=r.returncode,process_started=True)
 except OSError as error:row.update(returncode=None,process_started=False,launch_error=type(error).__name__+': '+str(error))
 row['log_sha256']=H(log.read_bytes());write(record,row);return row

def capability(compiler,strip,env,cwd,receipts):
 rows={}
 for label,command in [('compiler-version',[str(compiler/'rust/bin/rustc'),'--version','--verbose']),('cargo-version',[str(compiler/'rust/bin/cargo'),'--version','--verbose']),('target-cfg',[str(compiler/'rust/bin/rustc'),'--print','cfg','--target','sbf-solana-solana']),('target-spec',[str(compiler/'rust/bin/rustc'),'-Z','unstable-options','--print','target-spec-json','--target','sbf-solana-solana']),('target-libdir',[str(compiler/'rust/bin/rustc'),'--print','target-libdir','--target','sbf-solana-solana']),('strip-version',[str(strip),'--version'])]:
  row=run_once(label,command,env,cwd,receipts);assert row['returncode']==0,label;rows[label]=row
 cfg=(receipts/'target-cfg.log').read_text();spec=J(receipts/'target-spec.log');lib=Path((receipts/'target-libdir.log').read_text().strip())
 assert'target_family="solana"'in cfg and'target_feature="dynamic-frames"'not in cfg
 assert spec['features']=='+store-imm,+jmp-ext'and spec.get('cpu','generic')=='generic'
 assert lib.resolve()==(compiler/'rust/lib/rustlib/sbf-solana-solana/lib').resolve()and lib.is_dir()
 return {'commands':rows,'cfg':cfg,'spec':spec,'legacy_sysroot':str(lib),'legacy_sysroot_files':files(lib),'program_compilation_probes':0}

def authenticate_cache(source,cargo_home,sealed):
 lock=tomllib.loads((source/'Cargo.lock').read_text());packages={p['name']+'-'+p['version']:p for p in lock['package']if p.get('source')};approved={p['name']+'-'+p['version']:p for p in sealed};assert len(packages)==232 and set(packages)==set(approved)
 rows=[]
 for name,p in sorted(packages.items()):
  assert p['source']=='registry+https://github.com/rust-lang/crates.io-index'
  archives=list((cargo_home/'registry/cache').glob('*/'+name+'.crate'));roots=list((cargo_home/'registry/src').glob('*/'+name));assert len(archives)==len(roots)==1,name
  archive,root=archives[0],roots[0];assert H(archive.read_bytes())==p['checksum']==approved[name]['archive_sha256'];observed={}
  with tarfile.open(archive)as tf:
   for m in tf:
    if m.isdir():continue
    part=PurePosixPath(m.name);assert m.isfile()and part.parts[0]==name and'..'not in part.parts and not part.is_absolute();rel=str(PurePosixPath(*part.parts[1:]));assert rel not in observed
    raw=tf.extractfile(m).read();f=root/rel;assert not f.is_symlink()and f.read_bytes()==raw;observed[rel]=H(raw)
  assert observed==approved[name]['files'];extra=set(files(root))-set(observed);assert extra<= {'.cargo-ok','.cargo-checksum.json'},(name,extra)
  rows.append({'package':name,'archive_sha256':p['checksum'],'source_root':str(root),'verified_source_files':len(observed),'archive_member_hash_inventory_sha256':H(json.dumps(observed,sort_keys=True,separators=(',',':')).encode()),'cargo_markers':sorted(extra)})
 assert sum(x['verified_source_files']for x in rows)==7607
 return {'registry_roots':232,'source_files':7607,'packages':rows}

def diagnostics(raw):
 ansi=re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]');return [l for l in raw.decode('utf-8',errors='replace').splitlines()if ansi.sub('',l).lstrip().startswith('Error:')]

def compiled_log_links(raw,env,registry,successful):
 text=raw.decode('utf-8',errors='replace');commands=[]
 for line in text.splitlines():
  if 'Running `' not in line or '/rust/bin/rustc 'not in line:continue
  command=shlex.split(line.split('Running `',1)[1].removesuffix('`'));commands.append(command)
 roots=[c for c in commands if '--crate-name'in c and c[c.index('--crate-name')+1]=='donation_relay_source_proposal']
 if successful:
  assert len(roots)==1 and roots[0][0]==env['RUSTC'];root=roots[0]
  assert root[root.index('--target')+1]=='sbf-solana-solana'
  flags=[root[i+1]for i,x in enumerate(root[:-1])if x=='-C']
  assert {'opt-level=3','panic=abort','codegen-units=1','overflow-checks=on'}<=set(flags)
  assert not any(x.startswith(('lto','target-feature','target-cpu'))for x in flags)
  assert root.count('-Zremap-cwd-prefix=')==1 and not any(x.startswith('--remap-path-prefix')for x in root)
 prefix=str(Path(env['CARGO_HOME'])/'registry/src');pat=re.escape(prefix)+r'/[^/\s]+/([^/\s]+)/'
 used=set(re.findall(pat,'\n'.join(' '.join(c)for c in commands)));approved={r['package']:r for r in registry['packages']};assert used<=set(approved)
 return {'rustc_command_count':len(commands),'actual_root_commands':roots,'actual_compiled_registry_roots':sorted(used),'actual_compiled_source_files':sum(approved[n]['verified_source_files']for n in used),'all_compiled_registry_roots_authenticated':True,'root_flags_verified':successful,'compile_success_required_for_flag_acceptance':True,'log_sha256':H(raw)}

def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def assert_scratch_call_closure(ledger,c,o,u,start):
 # Consume actual targets plus complete-body/fixed-point witnesses for every edge.
 originals={r['start']:r for r in ledger['original-function-ledger.json']};candidates={r['start']:r for r in ledger['candidate-function-ledger.json']}
 witnesses={(r['original_ordinal'],r['candidate_index']):r for r in ledger['match-witnesses.json']}
 original=originals[36192];candidate=candidates[start];parent=witnesses[(original['ordinal'],candidate['index'])]
 assert original['bytes']==candidate['bytes']==608 and parent['recursive_call_shape_closed']
 assert [r['original']['offset']for r in parent['direct_calls']]==[160,560,600]
 checks=[]
 for edge in parent['direct_calls']:
  offset=edge['original']['offset'];assert edge['candidate']['offset']==offset
  expected={160:752688,560:36800,600:712224}[offset]
  ot=o.calls[36192+offset];ct=c.calls[start+offset]
  assert ot==expected==edge['original']['target']and ct==edge['candidate']['target']
  a,b=originals[ot],candidates[ct];assert edge['target_pair']==[a['ordinal'],b['index']]
  assert edge['normalized_body_pair']and edge['recursive_call_shape_closed']
  assert a['bytes']==b['bytes']and a['end']==ot+a['bytes']and b['end']==ct+b['bytes']
  assert ot in o.entries and next(x for x in o.entries if x>ot)==a['end']
  assert any(f['start']==ct and f['size']==b['bytes']for f in u.funcs)
  assert c.normalized[ct:ct+b['bytes']]==o.normalized[ot:ot+a['bytes']]and c.pattern(ct,b['bytes'])==o.pattern(ot,a['bytes'])
  child=witnesses[(a['ordinal'],b['index'])];assert child['recursive_call_shape_closed']
  for call in child['direct_calls']:
   k=call['original']['offset'];assert o.calls[ot+k]==call['original']['target']and c.calls[ct+k]==call['candidate']['target']
   assert call['normalized_body_pair']and call['recursive_call_shape_closed']
  checks.append({'body_offset':offset,'original_target':ot,'candidate_target':ct,'complete_bytes':a['bytes'],'candidate_symbol_and_original_entry_bounds':True,'complete_instruction_relocation_match':True,'recursive_direct_call_shape_checked':True,'child_direct_calls':child['direct_calls'],'data_and_indirect_limit':'These complete code/call checks do not establish full data objects, indirect calls or runtime ABI.'})
 return checks

def post_static(repo,work):
 # First target/candidate comparison and target-byte reads occur only here.
 mac=repo/MAC;target=repo/'evidence/dependencies/donation_relay/deployed.so';candidate=work/'build-01/candidate.so';symbols=work/'build-01/unstripped.so'
 assert H(target.read_bytes())==TARGET_SHA and H((mac/'build-01/candidate.so').read_bytes())==MAC_SHA
 for n,h in [('reference-build12-analyze.py',METHOD_SHA),('original-windows.json',WINDOWS_SHA),('match_helpers.py',ELF_METHOD_SHA)]:assert H((mac/n).read_bytes())==h,n
 method=load(mac/'reference-build12-analyze.py','linux_v148_full_ledger')
 class Inputs:
  def __truediv__(self,name):return {'original.so':target,'candidate.so':candidate,'unstripped.so':symbols,'original-windows.json':mac/'original-windows.json'}[name]
 ledger=method.analyze(Inputs());folder=work/'full-ledger';folder.mkdir()
 for name,value in ledger.items():
  b=method.encode(value);(folder/name).write_bytes(gzip.compress(b,mtime=0)if name.endswith('.gz')else b)
 elf=load(mac/'match_helpers.py','linux_v148_elf');c,o,u=elf.Elf(candidate),elf.Elf(target),elf.Elf(symbols);assert c.b[c.lo:c.hi]==u.b[u.lo:u.hi]
 results=[]
 for f in u.funcs:
  if not('driftsort_main'in f['name']and f['size']==608):continue
  st=f['start'];match=c.normalized[st:st+608]==o.normalized[36192:36800]and c.pattern(st,608)==o.pattern(36192,608)
  row={'name':f['name'],'start':st,'bytes':608,'entry_bounded':st in c.entries and next((x for x in c.entries if x>st),None)==st+608,'original608_instruction_relocation_match':match,'raw_equal_original':c.b[st:st+608]==o.b[36192:36800]}
  if match:
   row['actual_three_edge_closure']=assert_scratch_call_closure(ledger,c,o,u,st)
   assert c.b[st+584]==0x18 and c.relocations[st+584]=={'type':8,'symbol':''};ptr=struct.unpack_from('<I',c.b,st+588)[0]|struct.unpack_from('<I',c.b,st+596)[0]<<32
   v,n,line,col=struct.unpack_from('<QQII',c.b,ptr);start=v>>32;assert 0<=start<=len(c.b)and n<=len(c.b)-start;path=c.b[start:start+n];row['bounded_descriptor_prefix']={'file_offset':ptr,'prefix_bytes':24,'prefix_hex':c.b[ptr:ptr+24].hex(),'path_hex':path.hex(),'path_utf8':path.decode('utf-8',errors='backslashreplace'),'path_bytes':n,'line':line,'column':col,'full_object_extent_proven':False,'historical_os_unique':False}
   row['candidate_internal_calls']=c.callsites(st,608);row['original_internal_calls']=o.callsites(36192,608)
   ins=lambda at:struct.unpack_from('<BBhi',c.b,at)
   try:
    handle=c.calls[st+600];assert ins(handle)==(0x55,1,2,0)and ins(handle+8)==(0xbf,0x31,0,0)
    capacity=c.calls[handle+16];assert ins(capacity)==(0xbf,0x12,0,0)
    panic=c.calls[capacity+80];assert ins(panic)==(0x7b,0x2a,-16,0)and ins(panic+32)==(7,1,0,-24)
    unwind=c.calls[panic+40];pal=c.calls[unwind];assert c.relocations[pal]=={'type':10,'symbol':'custom_panic'}
    anchors=[st+584,st+600,handle,handle+8,handle+16,capacity,capacity+80,panic,panic+32,panic+40,unwind,pal]
    row['descriptor_pointer_flow']={'checked_to_external_custom_panic':True,'anchors':[{'pc':at,'raw':c.b[at:at+(16 if c.b[at]==0x18 else 8)].hex(),'call_target':c.calls.get(at),'relocation':c.relocations.get(at)}for at in anchors],'complete_object_extent_or_external_consumer_proven':False}
   except (AssertionError,KeyError):row['descriptor_pointer_flow']={'checked_to_external_custom_panic':False,'complete_object_extent_or_external_consumer_proven':False}
   try:
    wrapper=c.calls[st+160];callee=c.calls[wrapper+24]
    assert c.normalized[wrapper:wrapper+72]==o.normalized[752688:752760]and c.pattern(wrapper,72)==o.pattern(752688,72)
    assert c.b[callee:callee+352]==o.b[751104:751456]
    assert any(f['start']==wrapper and f['size']==72 and f['name']=='__multi3'for f in u.funcs)and any(f['start']==callee and f['size']==352 for f in u.funcs)
    assert wrapper in c.entries and callee in c.entries
    assert 752688 in o.entries and next(x for x in o.entries if x>752688)==752760 and 751104 in o.entries and next(x for x in o.entries if x>751104)==751456
    row['named_multiply_edge']={'checked':True,'body_offset':160,'wrapper':wrapper,'callee':callee,'wrapper_bytes':72,'raw_callee_bytes':352}
   except (AssertionError,KeyError,StopIteration):row['named_multiply_edge']={'checked':False}
  results.append(row)
 darwin=(mac/'build-01/candidate.so').read_bytes();linux=candidate.read_bytes()
 return {'summary':ledger['comparison-summary.json'],'linux_versus_darwin':{'raw_equal':linux==darwin,'linux_bytes':len(linux),'darwin_bytes':len(darwin),'common_position_different_bytes':sum(a!=b for a,b in zip(linux,darwin)),'linux_sha256':H(linux),'darwin_sha256':H(darwin),'not_a_semantic_distance':True},'driftsort':results,'darwin_control_sha256':MAC_SHA,'same_source_different_OS_distribution_and_strip_bytes':True,'runtime_executions':0,'readiness_or_promotion':False,'limit':'Complete instruction/relocation windows and bounded descriptor prefixes only; pointer/callee/indirect/full-data/runtime closure is not inferred.'}

def compile_and_strip(compiler,strip,source,env,cwd,work,frozen,post_auth,runner=run_once):
 receipts=work/'receipts';build=work/'build-01';build.mkdir(exist_ok=False)
 command=[str(compiler/'rust/bin/cargo'),'build','--manifest-path',str(source/'Cargo.toml'),'--release','--target','sbf-solana-solana','--locked','--offline','--verbose']
 offline={**env,'CARGO_NET_OFFLINE':'true'};r=runner('program-build',command,offline,cwd,receipts)
 state={'program_build_attempts':1,'compile_returncode':r['returncode'],'source_after_sha256':files(source),'source_unchanged':files(source)==frozen,'backend_diagnostics':diagnostics((receipts/'program-build.log').read_bytes())};write(work/'build-state.json',state)
 write(work/'registry-after.json',post_auth());assert state['source_unchanged'],'Frozen source changed during build'
 if r['returncode']!=0:return state
 compiled=Path(env['CARGO_TARGET_DIR'])/'sbf-solana-solana/release/donation_relay_source_proposal.so';assert compiled.is_file();shutil.copyfile(compiled,build/'unstripped.so')
 sr=runner('strip',[str(strip),'--strip-all',str(build/'unstripped.so'),str(build/'candidate.so')],offline,cwd,receipts);state['strip_returncode']=sr['returncode'];write(work/'build-state.json',state)
 return state

def publish(work):
 pub=work/'publication';pub.mkdir(exist_ok=False)
 # Fixed, reviewed allowlist only. No cache, toolchain, targets, archives or credentials.
 for name in ['plan.json','host.json','source-map.json','registry-before.json','registry-after.json','fetch-state.json','build-state.json','compiled-log-links.json','result.json','capability.json','compiler-tools.json','strip-tools.json','tools-after.json','static-comparison.json']:
  if(work/name).is_file():shutil.copy2(work/name,pub/name)
 if(work/'source-map.json').is_file():
  for name in J(work/'source-map.json'):
   part=PurePosixPath(name);assert not part.is_absolute()and'..'not in part.parts
   f=work/'source'/name
   if f.is_file()and not f.is_symlink():(pub/'source'/name).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,pub/'source'/name)
 for label in ['compiler','strip']:
  for name in ['release.json','acquisition.json']:
   f=work/(label+'-acquisition')/name
   if f.is_file():(pub/label).mkdir(exist_ok=True);shutil.copy2(f,pub/label/name)
 if(work/'receipts').is_dir():
  (pub/'receipts').mkdir()
  for label in ['compiler-version','cargo-version','target-cfg','target-spec','target-libdir','strip-version','cargo-fetch','program-build','strip']:
   for suffix in ['.log','.json']:
    f=work/'receipts'/(label+suffix)
    if not f.is_file():continue
    if suffix=='.log':(pub/'receipts'/(f.name+'.gz')).write_bytes(gzip.compress(f.read_bytes(),mtime=0))
    else:shutil.copy2(f,pub/'receipts'/f.name)
 for directory,names in [('build-01',['candidate.so','unstripped.so']),('full-ledger',['allocated-strip-identity.json','candidate-function-ledger.json','comparison-summary.json','coverage.json','match-ledger.json','match-witnesses.json','original-function-ledger.json','section-comparison.json','whole-file-residuals.json.gz'])]:
  for name in names:
   f=work/directory/name
   if f.is_file()and not f.is_symlink():(pub/directory).mkdir(exist_ok=True);shutil.copy2(f,pub/directory/name)
 shutil.copy2(Path(__file__),pub/'measurement-script.py');write(pub/'manifest.json',files(pub));return pub

def execute(p):
 assert platform.system()=='Linux'and platform.machine()=='x86_64';osrel=Path('/etc/os-release').read_text();assert re.search(r'^ID=ubuntu$',osrel,re.M)and re.search(r'^VERSION_ID="24.04"$',osrel,re.M)
 repo=Path(p['repo']);work=Path(p['output']);assert not work.resolve().is_relative_to(repo.resolve()),'Execute only in a fresh private path outside the checkout';work.mkdir(parents=True,exist_ok=False);write(work/'plan.json',p);write(work/'host.json',{'platform':platform.platform(),'uname':list(platform.uname()),'os_release':osrel});write(work/'source-map.json',p['frozen_source']);result={'state':'SETUP','program_build_attempts':0,'runtime_executions':0,'readiness_or_promotion':False};code=1
 try:
  shutil.copytree(repo/OLD/'source',work/'source');assert files(work/'source')==p['frozen_source']
  ca=fetch_asset(ASSETS['compiler'],work/'compiler-acquisition');sa=fetch_asset(ASSETS['strip'],work/'strip-acquisition');compiler=work/'compiler-tools';striproot=work/'strip-tools';cm=extract_verified(ca,compiler);sm=extract_verified(sa,striproot);ct=tools(compiler,cm);st=member(striproot,'llvm/bin/llvm-objcopy',sm);write(work/'compiler-tools.json',ct);write(work/'strip-tools.json',st)
  env=environment(compiler,work);strip=striproot/'llvm/bin/llvm-objcopy';sealed=J(repo/OLD/'launcher/resolved-source-archive-equality.json')
  with tempfile.TemporaryDirectory(prefix='relay-linux-v148-neutral-')as neutral:
   cwd=Path(neutral)
   for d in[cwd,*cwd.parents]:assert not(d/'.cargo/config').exists()and not(d/'.cargo/config.toml').exists()
   write(work/'capability.json',capability(compiler,strip,env,cwd,work/'receipts'))
   result['state']='FETCH';r=run_once('cargo-fetch',[str(compiler/'rust/bin/cargo'),'fetch','--manifest-path',str(work/'source/Cargo.toml'),'--locked'],env,cwd,work/'receipts')
   after=files(work/'source');write(work/'fetch-state.json',{'returncode':r['returncode'],'source_before_sha256':p['frozen_source'],'source_after_sha256':after,'source_unchanged':after==p['frozen_source'],'build_attempts':0});assert r['returncode']==0 and after==p['frozen_source'],'Fetch/setup failed; stop without program build'
   write(work/'registry-before.json',authenticate_cache(work/'source',work/'cargo-home',sealed));result['state']='BUILD'
   state=compile_and_strip(compiler,strip,work/'source',env,cwd,work,p['frozen_source'],lambda:authenticate_cache(work/'source',work/'cargo-home',sealed));result.update(state)
   write(work/'compiled-log-links.json',compiled_log_links((work/'receipts/program-build.log').read_bytes(),env,J(work/'registry-after.json'),state['compile_returncode']==0))
  aftertools={'compiler':tools(compiler,cm),'strip':member(striproot,'llvm/bin/llvm-objcopy',sm)};write(work/'tools-after.json',aftertools);assert aftertools=={'compiler':ct,'strip':st}
  if state['compile_returncode']==0 and state.get('strip_returncode')==0:
   write(work/'static-comparison.json',post_static(repo,work));result['state']='BACKEND_DIAGNOSTICS'if state['backend_diagnostics']else'MEASURED';code=1 if state['backend_diagnostics']else 0
  else:result['state']='COMPILE_OR_STRIP_FAILED'
 except Exception as error:result['error_type']=type(error).__name__;result['error']=str(error);result['exception_traceback']=traceback.format_exc()
 finally:
  for label,key in [('program-build','compile_returncode'),('strip','strip_returncode')]:
   receipt=work/'receipts'/(label+'.json')
   if receipt.exists():
    row=J(receipt);result[key]=row.get('returncode')
    if label=='program-build':result['program_build_attempts']=1;result['compiler_process_started']=row.get('process_started',False)
  write(work/'result.json',result);publish(work)
 return code

def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--repo',type=Path,required=True);a.add_argument('--output',type=Path,required=True);g=a.add_mutually_exclusive_group(required=True);g.add_argument('--dry-run',action='store_true');g.add_argument('--execute',action='store_true');args=a.parse_args();p=plan(args.repo,args.output)
 if args.dry_run:print(json.dumps(p,indent=2,sort_keys=True));return 0
 return execute(p)
if __name__=='__main__':raise SystemExit(main())
