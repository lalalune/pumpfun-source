from pathlib import Path
import gzip,hashlib,json,subprocess
W=Path(__file__).resolve().parent;R=W/'pumpfun-source';P=W/'mayhem-trade-arithmetic-lowering';D=P/'upstream-overflow';D.mkdir(exist_ok=False)
rev='a600dd2617cf9d062b0a602204fb8419e9e8c108';base='research/mayhem-sell-checked-value-price/';names=['manifest.json','source-inputs.json','builds/overflowing-product/symbols.so.gz','builds/overflowing-product/candidate.so.gz','builds/overflowing-product/result.json','builds/overflowing-product/overrides/src/instructions/pump_interface.rs.gz','builds/overflowing-product/overrides/src/state.rs.gz']
b=subprocess.run(['git','cat-file','--batch'],cwd=R,input=''.join(rev+':'+base+n+'\n' for n in names).encode(),capture_output=True,check=True).stdout;at=0;records={}
for n in names:
    end=b.index(b'\n',at);oid,kind,size=b[at:end].split();assert kind==b'blob';size=int(size);data=b[end+1:end+1+size];at=end+size+2;assert hashlib.sha1(b'blob '+str(size).encode()+b'\0'+data).hexdigest()==oid.decode();p=D/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);records[n]=dict(git_blob=oid.decode(),bytes=size,sha256=hashlib.sha256(data).hexdigest())
assert at==len(b);manifest=json.loads((D/'manifest.json').read_bytes());assert all(manifest[n]==r['sha256'] for n,r in records.items() if n!='manifest.json')
(P/'overflow-upstream-symbols.so').write_bytes(gzip.decompress((D/'builds/overflowing-product/symbols.so.gz').read_bytes()))
(D/'acquisition.json').write_text(json.dumps(dict(revision=rev,prefix=base,files=records),indent=2)+'\n',encoding='utf-8');print('Acquired authenticated prior overflowing-product artifact and source')
