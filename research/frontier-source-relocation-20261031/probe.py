"""Run real replay extraction and real validator admission, stopping before VM suites."""
import gzip, hashlib, importlib.util, io, json
from pathlib import Path
import sys, tarfile, tempfile
from unittest.mock import patch
repo=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(repo/'scripts'))
import pump_replay_macos_frontier as replay
import pump_validate_parallel as validator
sha=lambda b:hashlib.sha256(b).hexdigest()
class Admitted(Exception): pass
with tempfile.TemporaryDirectory(prefix='frontier-relocation-') as folder:
 root=Path(folder).resolve()
 original_prefix='work/pump-macos-qualification/candidate/source'
 files={'Cargo.toml':b'[workspace]\nmembers=["programs/pump"]\nresolver="2"\n',
        'Cargo.lock':b'version = 3\n',
        'programs/pump/Cargo.toml':b'[package]\nname="replay-fixture"\nversion="0.1.0"\nedition="2021"\n',
        'programs/pump/src/lib.rs':b'pub fn retained() -> u64 { 42 }\n'}
 inputs=root/'work/pump-macos-frontier-inputs'; (inputs/'candidate').mkdir(parents=True)
 candidate=b'local admission fixture; not an ELF or runtime claim'
 record={'returncode':0,'source_unchanged':True,'workspace_layout':True,
         'source_directory':'/original/checkout/'+original_prefix+'/programs/pump',
         'comparison':{'candidate_sha256':sha(candidate)},
         'source_sha256':{original_prefix+'/'+k:sha(v) for k,v in files.items()}}
 rawrecord=json.dumps(record).encode()
 for name,data in {'candidate.so':candidate,'unstripped.so':candidate,'build-comparison.json':rawrecord,'build-attempt.json':b'{}'}.items():
  (inputs/'candidate'/str(name+'.gz')).write_bytes(gzip.compress(data,mtime=0))
 with tarfile.open(inputs/'candidate/compiled-source.tar.gz','w:gz') as archive:
  for name,data in files.items():
   item=tarfile.TarInfo(name);item.size=len(data);archive.addfile(item,io.BytesIO(data))
 (inputs/'revision.txt').write_text('local-fixture\n')
 (inputs/'MANIFEST.json').write_text(json.dumps({str(p.relative_to(inputs)):sha(p.read_bytes()) for p in inputs.rglob('*') if p.is_file()}))
 replay.ROOT=validator.ROOT=root;replay.INPUT=inputs
 replay.BUILD=root/'work/pump-macos-qualification/candidate'
 replay.OUT=root/'work/pump-macos-frontier-runtime/evidence'
 observed={'original_workspace_absent':not (root/original_prefix).exists(),'validator_admitted':False}
 def stop_at_validator(command,**kwargs):
  path=Path(command[command.index('--build-comparison')+1]);derived=json.loads(path.read_text())
  crate=Path(command[command.index('--source-directory')+1])
  candidate_path=Path(command[command.index('--candidate')+1])
  sources,_,_=validator.validate_build_sources(derived,crate,candidate_path)
  assert all(sha((root/name).read_bytes())==digest for name,digest in sources.items())
  observed.update(validator_admitted=True,manifest_entries=len(sources),original_record_preserved=(path.parent/'build-comparison.json').read_bytes()==rawrecord)
  raise Admitted('actual validator admitted relocated compiler inputs; runtime intentionally not executed')
 try:
  with patch.object(replay.subprocess,'run',side_effect=stop_at_validator):replay.main()
 except BaseException as error:
  observed.update(error_type=type(error).__name__,error=str(error))
 print(json.dumps(observed,indent=2))
