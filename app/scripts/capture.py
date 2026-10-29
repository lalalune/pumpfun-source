#!/usr/bin/env python3
"""Capture public artifacts only; never submits forms or uses credentials."""
import concurrent.futures, sys, datetime, hashlib, html, json, os, pathlib, re, stat, tempfile, urllib.request, urllib.error, urllib.parse
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence' / 'web'
OBJECT_PATH = pathlib.PurePosixPath('evidence/web/objects')
UA = 'Googlebot'
PAGES = ['/', '/explore', '/leaderboard', '/live', '/go', '/mayhem', '/holder-rewards', '/create', '/perps', '/docs/fees', '/docs/privacy-policy', '/docs/terms-and-conditions']
HEADERS = {'server','x-powered-by','x-vercel-id','x-vercel-cache','cf-ray','cf-cache-status','content-type','content-security-policy','location','via','x-cache','x-amz-cf-id','x-amz-cf-pop'}

def public_asset(value,base,extensions):
    resolved,_=urllib.parse.urldefrag(urllib.parse.urljoin(base,value))
    parsed=urllib.parse.urlsplit(resolved)
    if parsed.scheme=='https' and parsed.netloc=='pump.fun' and parsed.path.endswith(extensions):return resolved
    return None
def atomic_write(target, body):
    """Publish complete bytes on the same filesystem; retain the old file on failure."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.' + target.name + '.', suffix='.tmp', delete=False) as stream:
            temporary = pathlib.Path(stream.name)
            stream.write(body)
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

def retain_manifest(body):
    """Keep the exact checkpoint before changing the selected manifest alias."""
    target = OUT / 'manifests' / (hashlib.sha256(body).hexdigest() + '.json')
    if target.exists():
        if target.read_bytes() != body:
            raise ValueError('Retained manifest differs from its content-addressed checkpoint')
    else:
        atomic_write(target, body)

def capture(url):
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    suffix = pathlib.PurePosixPath(urllib.parse.urlparse(url).path).suffix
    try:
        try: r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=35)
        except urllib.error.HTTPError as e: r = e
        try:
            body = r.read(); digest = hashlib.sha256(body).hexdigest()
            # A fresh response must not overwrite bytes referenced by an older manifest.
            target = OUT / 'objects' / (key + '-' + digest + (suffix if suffix in ['.js','.css','.woff2','.json','.txt','.svg','.png','.ttf','.woff'] else ''))
            atomic_write(target, body)
            return {'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':url,'final_url':r.url,'status':r.status,'path':target.relative_to(ROOT).as_posix(), 'bytes':len(body),'sha256':digest,'headers':{k.lower():v for k,v in r.headers.items() if k.lower() in HEADERS}}, body
        finally:
            r.close()
    except Exception as e: return {'url':url,'error':str(e)}, b''
class RetainedCaptureError(ValueError): pass
def retained_id(url): return hashlib.sha256(str(url).encode('utf-8',errors='backslashreplace')).hexdigest()[:12]
def retained_body(record,url):
    identity=retained_id(url)
    if not isinstance(record,dict): raise RetainedCaptureError(f'Retained capture {identity} invalid record')
    value=record.get('path')
    if not isinstance(value,str) or not value or '\x00' in value or '\\' in value:
        raise RetainedCaptureError(f'Retained capture {identity} invalid path')
    parts=value.split('/')
    pure=pathlib.PurePosixPath(value)
    if pure.is_absolute() or pathlib.PureWindowsPath(value).drive or any(part in ('','.','..') for part in parts) or pure.as_posix()!=value:
        raise RetainedCaptureError(f'Retained capture {identity} invalid path')
    try: relative=pure.relative_to(OBJECT_PATH)
    except ValueError: raise RetainedCaptureError(f'Retained capture {identity} path outside evidence objects') from None
    if not relative.parts: raise RetainedCaptureError(f'Retained capture {identity} invalid path')
    allowed=ROOT
    for part in OBJECT_PATH.parts:
        allowed/=part
        if allowed.is_symlink(): raise RetainedCaptureError(f'Retained capture {identity} symlink path rejected')
    try: allowed_resolved=allowed.resolve(strict=True)
    except (OSError,RuntimeError) as error: raise RetainedCaptureError(f'Retained capture {identity} object directory unavailable') from error
    if not allowed_resolved.is_dir(): raise RetainedCaptureError(f'Retained capture {identity} object directory unavailable')
    candidate=allowed
    for part in relative.parts:
        candidate/=part
        if candidate.is_symlink(): raise RetainedCaptureError(f'Retained capture {identity} symlink path rejected')
    try: resolved=candidate.resolve(strict=True)
    except FileNotFoundError as error: raise RetainedCaptureError(f'Retained capture {identity} object missing') from error
    except (OSError,RuntimeError) as error: raise RetainedCaptureError(f'Retained capture {identity} path cannot be resolved') from error
    try: resolved.relative_to(allowed_resolved)
    except ValueError: raise RetainedCaptureError(f'Retained capture {identity} path escaped evidence objects') from None
    # O_NONBLOCK lets a FIFO open without a writer so the regular-file check can reject it.
    flags=os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_CLOEXEC',0)|getattr(os,'O_NOFOLLOW',0)|getattr(os,'O_NONBLOCK',0)
    try: descriptor=os.open(resolved,flags)
    except OSError as error: raise RetainedCaptureError(f'Retained capture {identity} object unavailable') from error
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode): raise RetainedCaptureError(f'Retained capture {identity} target is not a regular file')
        with os.fdopen(descriptor,'rb') as handle:
            descriptor=None
            body=handle.read()
    finally:
        if descriptor is not None: os.close(descriptor)
    expected_bytes=record.get('bytes');expected_sha=record.get('sha256')
    if not isinstance(expected_bytes,int) or isinstance(expected_bytes,bool) or expected_bytes<0 or not isinstance(expected_sha,str):
        raise RetainedCaptureError(f'Retained capture {identity} invalid integrity metadata')
    if len(body)!=expected_bytes or hashlib.sha256(body).hexdigest()!=expected_sha:
        raise RetainedCaptureError(f'Retained capture {identity} integrity mismatch')
    return body
REUSE={}
def load_reuse(records,captured_at=None):
    validated={}
    for index,record in enumerate(records):
        url=record.get('url') if isinstance(record,dict) else None
        if not isinstance(url,str): raise RetainedCaptureError(f'Retained capture {retained_id(f"index:{index}")} invalid record')
        # A transport failure has no retained body to reuse; leave it queued for retry.
        if set(record)=={'url','error'} and isinstance(record['error'],str): continue
        if url in validated: raise RetainedCaptureError(f'Retained capture {retained_id(url)} duplicate URL')
        if 'status' in record and (type(record['status']) is not int or not 100 <= record['status'] <= 599):
            raise RetainedCaptureError(f'Retained capture {retained_id(url)} invalid HTTP status')
        retained_body(record,url)
        if isinstance(captured_at,str):
            record=dict(record);record.setdefault('captured_at',captured_at)
        validated[url]=record
    REUSE.update(validated)
def pool(urls):
    ordered=sorted(urls);retained={}
    for url in ordered:
        if url in REUSE:
            old=REUSE[url];retained[url]=(old,retained_body(old,url))
    def fetch(url):
        if url in retained: return retained[url]
        return capture(url)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex: return list(ex.map(fetch, ordered))
def main():
    if '--resume' in sys.argv and (OUT/'manifest.json').exists():
        previous=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
        load_reuse(previous['records'],previous.get('captured_at'))
    records=[]; pages=pool({'https://pump.fun'+p for p in PAGES} | {'https://docs.pump.fun/openapi.public.json','https://docs.pump.fun/llms-full.txt'})
    records.extend(r for r,b in pages)
    assets=set()
    for r,b in pages:
        if r.get('status')!=200 or not r['url'].startswith('https://pump.fun'): continue
        s=b.decode(errors='replace')
        for value in re.findall(r'(?:src|href)="(/[^"\s]+)"',s):
            asset=public_asset(html.unescape(value),r['url'],('.js','.css','.woff2','.svg','.png'))
            if asset:assets.add(asset)
    done=set(); waves=0
    while assets-done and waves<8:
        batch=assets-done; done|=batch; waves+=1
        results=pool(batch);records.extend(r for r,b in results)
        for r,b in results:
            if r.get('status')!=200: continue
            s=b.decode(errors='replace')
            # Follow literal Turbopack chunk paths and local font/image dependencies only.
            for path in re.findall(r'["\'(]((?:/_next/)?static/(?:immutable/)?(?:chunks|media)/[^"\'\s)]+)',s):
                asset=public_asset(path,'https://pump.fun/_next/',('.js','.css','.woff2'))
                if asset:assets.add(asset)
            if urllib.parse.urlsplit(r['url']).path.endswith('.css'):
                for relative in re.findall(r'url\([\"\']?([^\s)\"\']+)',s):
                    if not relative.startswith('data:'):
                        resolved=public_asset(relative,r['url'],('.woff2','.woff','.ttf','.png','.svg'))
                        if resolved:assets.add(resolved)
    OUT.mkdir(parents=True,exist_ok=True)
    manifest={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'user_agent':UA,'scope':PAGES,'exclusions':['support','terminal','mobile app','token/coin detail pages','pump-token'],'records':records,'limits':{'asset_discovery_waves':8,'waves_used':waves,'unfetched_discovered':sorted(assets-done)}}
    selected = OUT / 'manifest.json'
    if selected.exists():
        retain_manifest(selected.read_bytes())
    encoded = (json.dumps(manifest,indent=2)+'\n').encode('utf-8')
    retain_manifest(encoded)
    atomic_write(selected, encoded)
    print(json.dumps({'records':len(records),'successful':sum(r.get('status')==200 for r in records),'bytes':sum(r.get('bytes',0) for r in records),'remaining':len(assets-done)}))
if __name__=='__main__': main()
