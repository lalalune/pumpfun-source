import pathlib,json,hashlib,base64,tarfile
root=pathlib.Path(__file__).resolve().parents[1]
m=json.loads((root/'evidence/web/manifest.json').read_text(encoding='utf-8'))
records=m['records']
for name in ['api-probes.json','source-map-probes.json']:
 records += json.loads((root/'evidence'/name).read_text(encoding='utf-8'))
objects_root=root/'evidence/web/objects'
actual_objects={p.relative_to(root).as_posix() for p in objects_root.rglob('*') if p.is_file()} if objects_root.exists() else set()
referenced_objects={r['path'] for r in records if 'path' in r and r['path'].startswith('evidence/web/objects/')}
if actual_objects!=referenced_objects:
 raise ValueError(f"Captured object inventory differs from records: unreferenced={sorted(actual_objects-referenced_objects)}, missing={sorted(referenced_objects-actual_objects)}")
for r in records:
 if 'path' not in r: continue
 relative=r['path']
 if not isinstance(relative,str) or not relative or '\\' in relative or pathlib.PurePosixPath(relative).is_absolute() or ':' in relative or any(part in {'', '.', '..'} for part in relative.split('/')):
  raise ValueError('Unsafe capture path')
 target=root/relative
 if not target.resolve().is_relative_to(root.resolve()):
  raise ValueError('Escaping capture path')
 body=target.read_bytes()
 if hashlib.sha256(body).hexdigest()!=r['sha256']:
  raise ValueError(f"Captured object SHA-256 mismatch: {r['path']}")
 # Older probe records may omit byte counts; validate every count that is present.
 if 'bytes' in r and (type(r['bytes']) is not int or r['bytes']<0 or len(body)!=r['bytes']):
  raise ValueError(f"Captured object byte count mismatch: {r['path']}")
meta=json.loads((root/'evidence/sdk/registry.json').read_text(encoding='utf-8'))
def sdk_identity(value, source):
 if not isinstance(value,dict) or (value.get('name'),value.get('version'))!=('@pump-fun/pump-sdk','4.3.1'):
  raise ValueError(f'SDK package identity mismatch: {source}')
sdk_identity(meta,'registry.json')
archive=root/'evidence/sdk/pump-sdk-4.3.1.tgz'
if 'sha512-'+base64.b64encode(hashlib.sha512(archive.read_bytes()).digest()).decode()!=meta['dist']['integrity']:
 raise ValueError('SDK archive npm integrity mismatch')
expected_sources=set()
with tarfile.open(archive) as tar:
 package_metadata=[member for member in tar.getmembers() if member.name=='package/package.json']
 if len(package_metadata)!=1 or not package_metadata[0].isfile():
  raise ValueError('SDK package identity requires one regular archive package.json')
 sdk_identity(json.loads(tar.extractfile(package_metadata[0]).read()),'archive package.json')
 sdk_identity(json.loads((root/'packages/sdk/package.json').read_text(encoding='utf-8')),'local package.json')
 for member in tar.getmembers():
  if member.name.startswith('package/src/') and member.isfile():
   relative=member.name.removeprefix('package/src/')
   if relative in expected_sources: raise ValueError(f'Duplicate SDK source archive member: {relative}')
   expected_sources.add(relative)
   if tar.extractfile(member).read()!=(root/'packages/sdk'/member.name.removeprefix('package/')).read_bytes():
    raise ValueError(f'SDK source bytes differ from archive: {member.name}')
source_root=root/'packages/sdk/src'
actual_sources={path.relative_to(source_root).as_posix() for path in source_root.rglob('*') if path.is_file()}
if actual_sources != expected_sources:
 raise ValueError(f'SDK source inventory differs from archive: extra={sorted(actual_sources-expected_sources)}, missing={sorted(expected_sources-actual_sources)}')
print(f"Verified {len(records)} captured objects, npm integrity, and unchanged SDK sources")
