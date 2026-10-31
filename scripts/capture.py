#!/usr/bin/env python3
"""Read-only finalized RPC capture. Refuses replacing existing evidence."""
import argparse, base64, datetime, hashlib, json, pathlib, shutil, struct, tempfile, time, urllib.request
ALPHABET='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
def b58(data):
    n=int.from_bytes(data,'big'); s=''
    while n: n,r=divmod(n,58); s=ALPHABET[r]+s
    return '1'*(len(data)-len(data.lstrip(b'\0')))+s
def sha(data): return hashlib.sha256(data).hexdigest()
def check(ok, message="capture check failed"):
    # Explicit check instead of `assert`: `python -O` / `-OO` strips asserts,
    # which let a capture publish evidence after the deployed program changed
    # between reads.
    if not ok:
        raise AssertionError(message)
def rpc(url,method,params):
    body=json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params)).encode()
    for attempt in range(6):
        try:
            req=urllib.request.Request(url,data=body,headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=120) as r: result=json.load(r)
            if 'error' in result: raise RuntimeError(result['error'])
            return result['result']
        except Exception:
            if attempt==5: raise
            time.sleep(2**attempt)
def account(url,key,minimum=None):
    config={'encoding':'base64','commitment':'finalized'}
    if minimum is not None: config['minContextSlot']=minimum
    r=rpc(url,'getAccountInfo',[key,config]); a=r['value']
    if a is None: raise ValueError('missing account '+key)
    return r,base64.b64decode(a['data'][0],validate=True)
def _capture_to_directory(url,name,key,out):
    out.mkdir(parents=True,exist_ok=True)
    before,p=account(url,key)
    if before['value']['owner']=='BPFLoader2111111111111111111111111111111111':
        check(before['value']['executable'] and p[:4]==b'\x7fELF')
        after,p2=account(url,key,before['context']['slot']); check(p==p2)
        (out/'program-account.bin').write_bytes(p); (out/'deployed.so').write_bytes(p)
        report={'program':key,'owner':before['value']['owner'],'loader':'legacy-v2','last_deploy_slot':None,'upgrade_authority':None,'context_slots':[before['context']['slot'],after['context']['slot']],'commitment':'finalized','captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'genesis_hash':rpc(url,'getGenesisHash',[]),'program_sha256':sha(p),'payload_sha256':sha(p),'payload_bytes':len(p)}
        (out/'capture.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n'); print(name,'legacy-v2',len(p),sha(p),flush=True); return
    check(before['value']['executable'] and before['value']['owner']=='BPFLoaderUpgradeab1e11111111111111111111111')
    check(len(p)==36 and struct.unpack_from('<I',p)[0]==2)
    pd=b58(p[4:36]); data,d=account(url,pd,before['context']['slot'])
    check(data['value']['owner']==before['value']['owner'] and not data['value']['executable'])
    check(struct.unpack_from('<I',d)[0]==3 and d[12] in (0,1))
    slot=struct.unpack_from('<Q',d,4)[0]; payload=d[45:]; check(payload[:4]==b'\x7fELF')
    # Re-read pointer and metadata after large fetch; reject an intervening upgrade.
    after,p2=account(url,key,data['context']['slot'])
    meta=rpc(url,'getAccountInfo',[pd,{'encoding':'base64','commitment':'finalized','minContextSlot':after['context']['slot'],'dataSlice':{'offset':0,'length':45}}])
    check(p==p2 and base64.b64decode(meta['value']['data'][0])==d[:45], 'deployment changed during capture')
    (out/'program-account.bin').write_bytes(p); (out/'programdata-account.bin').write_bytes(d); (out/'deployed.so').write_bytes(payload)
    # Avoid publishing credentials if caller supplies a private RPC URL.
    report={'program':key,'programdata':pd,'owner':before['value']['owner'],'last_deploy_slot':slot,'upgrade_authority':b58(d[13:45]) if d[12] else None,'context_slots':[before['context']['slot'],data['context']['slot'],after['context']['slot'],meta['context']['slot']],'commitment':'finalized','captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'genesis_hash':rpc(url,'getGenesisHash',[]),'program_sha256':sha(p),'programdata_sha256':sha(d),'payload_sha256':sha(payload),'payload_bytes':len(payload),'programdata_bytes':len(d),'lamports':data['value']['lamports']}
    (out/'capture.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n'); print(name,slot,len(payload),sha(payload),flush=True)
def capture(url,name,key,out):
    out=pathlib.Path(out)
    if out.is_symlink() or out.exists():raise FileExistsError('capture output already exists: '+str(out))
    out.parent.mkdir(parents=True,exist_ok=True)
    stage=pathlib.Path(tempfile.mkdtemp(prefix='.'+out.name+'.capture-',dir=out.parent))
    try:
        _capture_to_directory(url,name,key,stage)
        if out.is_symlink() or out.exists():raise FileExistsError('capture output appeared during capture: '+str(out))
        # The destination can appear after the check above. Plain POSIX rename
        # replaces an empty directory, so publication must reject it atomically.
        from deep_disassembly import rename_directory
        rename_directory(stage,out)
    finally:
        if stage.exists():shutil.rmtree(stage)
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--rpc',default='https://api.mainnet-beta.solana.com'); ap.add_argument('--output',default='evidence/original'); args=ap.parse_args()
    from analyze import program_addresses
    for name,key in program_addresses().items(): capture(args.rpc,name,key,pathlib.Path(args.output)/name)
