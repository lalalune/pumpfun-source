"""Fresh offline historical-source proc macro; no prior host target directory."""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import argparse,gzip,hashlib,importlib.util,io,json,os,re,subprocess,tarfile,time
HERE=Path(__file__).resolve().parent
def require(ok,msg):
 if not ok:raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def identity(b):return dict(bytes=len(b),sha256=sha(b))
def save(p,x):p.write_bytes((json.dumps(x,indent=2)+'\n').encode())
def safe(n):
 p=PurePosixPath(n);require(n and not p.is_absolute() and '..' not in p.parts and ':' not in n and '\\' not in n and p.as_posix()==n,'unsafe path');return n
def unpack(b):
 result={}
 with tarfile.open(fileobj=io.BytesIO(b),mode='r:*') as t:
  for m in t:
   if m.isdir():continue
   require(m.isfile(),'nonregular tar member');name=safe(m.name);require(name not in result,'duplicate tar member');result[name]=t.extractfile(m).read()
 return result
def snapshot(root):return {p.relative_to(root).as_posix():identity(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}
def build(args):
 require(os.name=='nt','Windows native host compiler required');O=args.output.resolve();O.mkdir(parents=True,exist_ok=False);result=dict(status='STARTED',target_executions=0);start=time.monotonic()
 try:
  C=HERE/'controller';I=HERE/'host-inputs';spec=importlib.util.spec_from_file_location('target_controller',C/'build.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
  pins=json.loads((I/'inputs.json').read_text());require(snapshot(I)==dict(pins,**{'inputs.json':identity((I/'inputs.json').read_bytes())}),'host input pins')
  sdk=args.sdk.resolve();vendor=args.vendor.resolve();vc=args.msvc.resolve();kit=args.windows_sdk.resolve()
  c.pin(sdk,c.read(C/'sdk-components.json.gz')['files']);vendor_count=c.vendor_check(vendor,C)
  expected={Path(k.replace('\\','/')).name:v for k,v in c.read(C/'host-tools.json').items()};actual={p.name:c.sha(p) for p in [sdk/'rust/bin/rustc.exe',sdk/'rust/bin/cargo.exe',vc/'bin/Hostx64/x64/link.exe']};require(all(expected[n]==h for n,h in actual.items()),'host tools differ')
  source=unpack((I/'historical-source.tar.gz').read_bytes());tree=json.loads((I/'source-tree.json').read_text());require(tree['revision']=='c0077c2a7de64361f451735ac89118bc89f1c277' and len(source)==121,'historical source set')
  for r in tree['files']:
   b=source[r['path']];require(len(b)==r['size'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['sha'],'historical blob')
  require(set(source)=={r['path'] for r in tree['files']},'historical file inventory')
  before=source['Cargo.toml'];after,n=re.subn(rb'members = \[.*?\]',b'members = ["lang/attribute/program", "lang/syn", "idl", "idl/spec"]',before,count=1,flags=re.S);require(n==1 and before!=after,'workspace adaptation');after+=b'\n[patch.crates-io]\n'
  packs=json.loads((I/'supplement-packages.json').read_text());receipts={x['name']:x for x in json.loads((I/'supplement-receipts.json').read_text())};supplement_files={}
  for r in packs:
   name=r['name']+'-'+r['version'];blob=(I/'archives'/(name+'.crate')).read_bytes();require(sha(blob)==r['checksum']==receipts[name]['archive_sha256'],'supplement archive checksum');files=unpack(blob);files={n[len(name)+1:]:b for n,b in files.items() if n.startswith(name+'/')};require({n:identity(b) for n,b in files.items()}==receipts[name]['files'],'supplement file inventory')
   for n,b in files.items():
    p=O/'supplements'/name/safe(n);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
   supplement_files.update({'supplements/'+name+'/'+n:identity(b) for n,b in files.items()})
   after+=(r['name']+' = { path = '+json.dumps('../supplements/'+name)+' }\n').encode()
  source['Cargo.toml']=after;source['Cargo.lock']=(I/'resolved-Cargo.lock').read_bytes();S=O/'source'
  for n,b in source.items():
   p=S/safe(n);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  initial=snapshot(S);home=O/'cargo-home';home.mkdir();(O/'temp').mkdir();require(not (O/'target').exists(),'target directory already exists')
  (home/'config.toml').write_bytes(('[source.crates-io]\nreplace-with="locked-vendor"\n[source.locked-vendor]\ndirectory='+json.dumps(str(vendor))+'\n[net]\noffline=true\n').encode())
  env={k:os.environ[k] for k in ['SystemRoot','WINDIR','SystemDrive','COMSPEC','PROCESSOR_ARCHITECTURE'] if k in os.environ};system=Path(os.environ['SystemRoot'])
  env.update(PATH=os.pathsep.join(map(str,[sdk/'rust/bin',sdk/'llvm/bin',vc/'bin/Hostx64/x64',kit/'bin'/args.kit_version/'x64',system/'System32'])),LIB=os.pathsep.join(map(str,[vc/'lib/x64',kit/'Lib'/args.kit_version/'ucrt/x64',kit/'Lib'/args.kit_version/'um/x64'])),INCLUDE=os.pathsep.join(map(str,[vc/'include',*[kit/'Include'/args.kit_version/n for n in ['ucrt','shared','um','winrt']]])),RUSTC=str(sdk/'rust/bin/rustc.exe'),RUSTDOC=str(sdk/'rust/bin/rustdoc.exe'),CARGO_TARGET_X86_64_PC_WINDOWS_MSVC_LINKER=str(vc/'bin/Hostx64/x64/link.exe'),CARGO_HOME=str(home),CARGO_TARGET_DIR=str(O/'target'),CARGO_NET_OFFLINE='true',TEMP=str(O/'temp'),TMP=str(O/'temp'))
  command=[str(sdk/'rust/bin/cargo.exe'),'build','--locked','--offline','--manifest-path',str(S/'Cargo.toml'),'--release','-p','anchor-attribute-program','--verbose']
  save(O/'launch.json',dict(command=command,cwd=str(S),environment=env,source_inputs=initial,supplement_inputs=supplement_files,target_directory_initially_absent=True,checked_tools=actual,vendor_packages=vendor_count,controller_sha256=sha(Path(__file__).read_bytes()),input_pins=pins,scope='Historical Anchor macro/syn/IDL/spec source, resolved diagnostic lock and registry vendor; fresh host dependencies, no prior host artifacts. Target runtime remains1.0.0.'))
  with (O/'stdout.log').open('wb') as out,(O/'stderr.log').open('wb') as err:r=subprocess.run(command,cwd=S,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
  require(r.returncode==0,'host build failed');require(snapshot(S)==initial,'host source changed');require(all(identity((O/n).read_bytes())==v for n,v in supplement_files.items()),'supplement changed');c.vendor_check(vendor,C)
  release=O/'target/release';macro=release/'anchor_attribute_program.dll';deps={p.relative_to(release).as_posix():c.sha(p) for p in sorted((release/'deps').iterdir()) if p.suffix in ['.dll','.rlib','.rmeta']};binding=dict(macro=dict(path=macro.name,sha256=c.sha(macro)),host_dependencies=deps);save(O/'macro-binding.json',binding)
  stderr=(O/'stderr.log').read_text(errors='replace');compiles=[line for line in stderr.splitlines() if 'Running `' in line and '--crate-name ' in line];require(len(compiles)==42,'host compilation command count');save(O/'compile-commands.json',compiles)
  result.update(status='SUCCEEDED',returncode=0,source_unchanged=True,supplements_unchanged=True,vendor_rechecked=True,compilations=len(compiles),macro=identity(macro.read_bytes()),host_dependency_files=len(deps),logs={n:identity((O/n).read_bytes()) for n in ['stdout.log','stderr.log']})
 except Exception as exc:
  result.update(status='FAILED',error=repr(exc));raise
 finally:
  result.update(elapsed_seconds=time.monotonic()-start,finished_at=datetime.now(timezone.utc).isoformat());save(O/'result.json',result);print(result,flush=True)
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__)
 for n in ['sdk','vendor','msvc','windows-sdk','output']:a.add_argument('--'+n,type=Path,required=True)
 a.add_argument('--kit-version',default='10.0.26100.0');build(a.parse_args())
