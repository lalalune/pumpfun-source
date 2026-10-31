"""Bounded H1 negative replay. Reads fixed captures; never runs project code."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, io, json, struct, sys, tarfile, zipfile

HERE = Path(__file__).resolve().parent
def need(ok, message):
    if not ok: raise ValueError(message)
def sha(data): return hashlib.sha256(data).hexdigest()
def js(data): return json.loads(data)
def safe(name):
    p = PurePosixPath(name)
    return not p.is_absolute() and '..' not in p.parts and str(p) == name
def pinned(path, expected):
    data = path.read_bytes()
    need(len(data) == expected['bytes'] and sha(data) == expected['sha256'], str(path))
    return data
def zip_members(data):
    result = {}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in archive.infolist():
            need(safe(member.filename) and member.filename not in result and not member.is_dir()
                 and not member.flag_bits & 1 and ((member.external_attr >> 16) & 0o170000) in (0,0o100000), 'safe ZIP')
            result[member.filename] = archive.read(member)
    need(len(result) == 43, 'normal 43-member artifact')
    return result
def tar_members(data):
    result = {}
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for member in archive:
            need(safe(member.name) and member.isfile() and member.name not in result, 'safe TAR')
            result[member.name] = (archive.extractfile(member).read(), bool(member.mode & 0o111))
    return result
def elf(data):
    need(data[:7] == b'\x7fELF\x02\x01\x01', 'ELF64LE')
    h = struct.unpack_from('<16sHHIQQQIHHHHHH', data)
    need(h[1] == 3 and h[2] == 263 and h[11] == 64 and h[13] < h[12], 'SBF geometry')
    rows = [struct.unpack_from('<IIQQQQIIQQ', data, h[6] + i*64) for i in range(h[12])]
    def payload(row):
        need(row[4]+row[5] <= len(data), 'section bounds')
        return data[row[4]:row[4]+row[5]]
    names = payload(rows[h[13]]); sections = {}
    for row in rows:
        name = names[row[0]:names.index(b'\0', row[0])].decode()
        need(name not in sections, 'unique section')
        sections[name] = row
    symbols = []
    for row in rows:
        if row[1] != 2: continue
        strings = payload(rows[row[6]])
        need(row[9] == 24, 'symbol width')
        for p in range(row[4], row[4]+row[5], 24):
            n, info, other, index, address, size = struct.unpack_from('<IBBHQQ', data, p)
            if info & 15 == 2 and size:
                symbols.append({'address':address,'bytes':size,'name':strings[n:strings.index(b'\0',n)].decode()})
    return sections, symbols
def decode(data, address, symbols):
    names = {r['address']:r['name'] for r in symbols}; rows = []; p = 0
    widths = {0x60:4,0x68:2,0x70:1,0x78:8}
    while p < len(data):
        op, registers, displacement, immediate = struct.unpack_from('<BBhi', data, p)
        width = 16 if op == 0x18 else 8; need(p+width <= len(data), 'logical boundary')
        dst, src = registers & 15, registers >> 4
        r = dict(offset=p,va=address+p,opcode=op,dst=dst,src=src,displacement=displacement,
                 immediate=immediate,bytes=width,raw=data[p:p+width].hex())
        if op == 0x85 and src == 1 and immediate != -1:
            r['callTarget'] = address+p+8+8*immediate; r['callName'] = names.get(r['callTarget'])
        elif op == 0x85: r['opaqueCall'] = True
        elif op & 7 in (5,6) and op & 0xf0 not in (0x80,0x90): r['jump'] = p+8+8*displacement
        if op & 7 in (1,2,3) and op & 0xf8 in widths:
            r.update(memoryWidth=widths[op & 0xf8],memoryKind='read' if op & 7 == 1 else 'write',memoryBase=src if op & 7 == 1 else dst)
        rows.append(r); p += width
    return rows
def reaching(rows):
    by = {r['offset']:r for r in rows}; pred = {p:[] for p in by}
    for r in rows:
        nxt = r['offset']+r['bytes']
        targets = [] if r['opcode'] == 0x95 else [r['jump']] + ([nxt] if r['opcode'] & 0xf0 else []) if 'jump' in r else [nxt]
        for q in targets:
            if q in by: pred[q].append(r['offset'])
    def query(pc, register=None, byte=None):
        pending = list(pred[pc]); seen = set(); found = set(); entry = not pending
        while pending:
            p = pending.pop()
            if p in seen: continue
            seen.add(p); r = by[p]
            if register is not None:
                defines = register <= 5 if r['opcode'] in (0x85,0x8d) else r['dst'] == register and (r['opcode'] == 0x18 or r['opcode'] & 7 in (1,4,7))
            else:
                defines = r.get('memoryKind') == 'write' and r.get('memoryBase') == 10 and r['displacement'] <= byte < r['displacement']+r['memoryWidth']
            if defines: found.add(p)
            else: entry |= not pred[p]; pending.extend(pred[p])
        return dict(at=pc,definitions=sorted(found),entryWithoutDefinition=entry,**({'register':register} if register is not None else {'fpByte':byte}))
    return by, query
def caller_values(by, tag):
    """Finite emitted-region evaluation; fork unknown classification branches."""
    pending = [(0x498,{9:None})]; outputs = set(); steps = 0
    while pending:
        pc, regs = pending.pop(); steps += 1; need(steps < 100, 'finite caller region')
        if pc == 0x518: outputs.add(regs.get(8)); continue
        r = by[pc]; op,d,s = r['opcode'],r['dst'],r['src']; nxt = pc+r['bytes']; regs=dict(regs)
        if pc == 0x498: need(op==0x79, 'hopt reload'); regs[d]=tag
        elif op == 0xbf: regs[d]=regs.get(s)
        elif op == 0xb7: regs[d]=r['immediate']
        elif op == 0x57: regs[d]=None if regs.get(d) is None else regs[d]&r['immediate']
        elif op in (0x15,0x55):
            value=regs.get(d)
            if value is None: pending.extend([(r['jump'],dict(regs)),(nxt,dict(regs))]); continue
            equal=value==r['immediate']; pending.append((r['jump'] if equal == (op==0x15) else nxt,regs)); continue
        else: raise ValueError('unsupported finite caller-region instruction')
        pending.append((nxt,regs))
    return outputs
def run(args):
    pins = js((HERE/'inputs.json').read_bytes())
    native = zip_members(pinned(args.native_zip,pins['inputs']['nativeZip']))
    control = zip_members(pinned(args.control_zip,pins['inputs']['controlZip']))
    capsule = tar_members(pinned(args.capsule,pins['inputs']['capsule']))
    c = lambda name: capsule[name][0]
    manifest = js(c('CAPSULE-MANIFEST.json'))
    need(set(capsule) == set(manifest['files']) | {'CAPSULE-MANIFEST.json'}, 'capsule domain')
    for name, expected in manifest['files'].items(): need(len(c(name)) == expected['bytes'] and sha(c(name)) == expected['sha256'], name)
    need(manifest['source'] == pins['source'] and manifest['operational'] == pins['operational'], 'source cohort')
    for name, expected in pins['images'].items(): need(sha(native[name]) == expected, name)
    src, old = js(native['program-source-inputs.json']), js(control['program-source-inputs.json'])
    a, b = ({r['path']:r for r in source['files']} for source in (src,old))
    leaf = 'programs/pump/src/creator/admin_cto.rs'
    need(src['base'] == pins['source'] and old['base'] == pins['parent'] and len(a) == len(b) == 141 and set(a) == set(b), 'genuine source141')
    need([name for name in a if a[name] != b[name]] == [leaf], 'sole changed source')
    selected=js(native['source-inputs.json']); stage=js(native['compiled-workspace-inputs.json'])
    need(selected['sha256']==pins['sourceVectorSHA256'] and sha(json.dumps(selected['files'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())==pins['sourceVectorSHA256'], 'selected source vector')
    need(len(stage)==142 and sha(json.dumps(stage,sort_keys=True,separators=(',',':')).encode())==pins['stageVectorSHA256'], 'stage142 vector')
    need(len(js(native['toolchain-source-inputs.json'])['files'])==236, 'CORE236 count')
    need(native['toolchain-source-inputs.json'] == control['toolchain-source-inputs.json'] or js(native['toolchain-source-inputs.json'])['files'] == js(control['toolchain-source-inputs.json'])['files'], 'CORE236 unchanged')
    for members, index in ((native,a),(control,b)):
        source = tar_members(members['program-source.tar.gz']); need(set(source) == set(index), 'source TAR domain')
        for name, row in index.items():
            value, executable = source[name]
            need(len(value) == row['bytes'] and sha(value) == row['sha256'] and executable == (row['mode'] == '100755'), 'typed source TAR '+name)
    before = tar_members(control['program-source.tar.gz'])[leaf][0]
    after = tar_members(native['program-source.tar.gz'])[leaf][0]
    need(after == c('program-source/admin_cto.rs'), 'actual compiled leaf')
    aa,bb = before.splitlines(keepends=True), after.splitlines(keepends=True)
    need(len(aa)==len(bb)==772 and [i+1 for i,(x,y) in enumerate(zip(aa,bb)) if x!=y] == [283,289,339], 'exact three source lines')
    need((HERE/'SOURCE.patch').read_bytes() == c('source-plan/proposal/source.patch'), 'retained patch')
    report = js(c('work/root/CURRENT-ELF-ADMISSION.json')); official = js(c('work/root/admission/official-score/score.json'))
    need(official['windows'] == js(native['score.json'])['windows'], 'actual native versus one official score')
    windows, reference = official['windows'], js(control['score.json'])['windows']
    need(set(windows) == set(reference) and len(windows) == 1035, 'all score rows')
    losses = {kind:[hex(int(k)) for k in sorted(windows,key=int) if reference[k][kind] and not windows[k][kind]] for kind in ('raw','normalized')}
    need(len(losses['raw'])==687 and not losses['normalized'] and sum(r['raw'] for r in windows.values())==347 and sum(r['normalized'] for r in windows.values())==1034, 'negative score arithmetic')
    need(report['comparison']['rawLosses']==losses['raw'] and report['membershipQualification']=='REJECTED_RAW_OR_NORMALIZED_LOSS', 'actual rejection')
    need(report['officialScore']['jsonSha256'] == sha(c('work/root/admission/official-score/score.json')), 'official score binding')
    secondary = js(c('work/secondary-admission-reader/actual-review/REVIEW.json'))
    need(len(secondary['checks'])==39 and all(r['pass'] for r in secondary['checks']), 'retained secondary checks; not independently rerun')
    sections, symbols = elf(native['unstripped.so']); text = sections['.text']
    ct = [s for s in symbols if 'admin_cto7execute17h' in s['name']]
    need(len(ct)==1 and ct[0]['bytes']==26776, 'unique H1 CTO')
    ct = ct[0]; start = text[4]+ct['address']-text[3]
    body = native['unstripped.so'][start:start+ct['bytes']]; need(sha(body)==pins['h1BodySHA256'], 'actual H1 body')
    cache = js(c('work/native-inspection/actual/H1-PREFIX.json')); end = cache['prefix']['bytes']
    rows = decode(body[:end],ct['address'],symbols)
    need(rows == cache['rows'] and sha(body[:end])==pins['h1PrefixSHA256'], 'raw prefix replay')
    need('prepare_bonding_curve' in (rows[-1].get('callName') or '') and not any('prepare_bonding_curve' in (r.get('callName') or '') for r in rows[:-1]), 'first named prepare boundary')
    by, query = reaching(rows); mechanism = js(c('work/native-inspection/actual/HOPT-MECHANISM.json'))
    queries = mechanism['registerQueries']+mechanism['incomingRawOption']['byteQueries']+mechanism['incomingRawOption']['copyQueries']+mechanism['sharedProjection']['byteQueries']
    for q in queries: need(query(q['at'],q.get('register'),q.get('fpByte'))==q, 'H1 reaching query')
    need(not any(r['opcode'] in (0x54,0x57) and r['immediate'] in (253,-3) for r in rows), 'FD/-3 absent in prefix')
    need(by[0x4d8]['opcode']==by[0x7e0]['opcode']==by[0x1868]['opcode']==0x57 and all(by[p]['immediate']==1 for p in (0x4d8,0x7e0,0x1868)), 'actual AND1 operands')
    need(by[0x4b8]['opcode']==0x15 and by[0x4b8]['immediate']==2 and by[0x4b8]['jump']==0x4f0, 'explicit None branch retained')
    valid_tags=[]
    for case,tag in [('None',2),('Some(false)',0),('Some(true)',1)]:
        actual=caller_values(by,tag); need(actual=={tag&1}, 'emitted caller projection for '+case)
        valid_tags.append({'case':case,'input':tag,'emittedStoredHolder':sorted(actual)})
    original = pinned(args.repo / pins['original']['path'],pins['original'])
    os, _ = elf(original); t=os['.text']; p=t[4]+pins['original']['bodyVA']-t[3]
    ob=original[p:p+pins['original']['bodyBytes']]; need(sha(ob)==pins['original']['bodySHA256'], 'original body seal')
    orows=decode(ob[:pins['original']['prefixBytes']],pins['original']['bodyVA'],[]); oby, oq=reaching(orows)
    need(oby[0x10]['opcode']==0x7b and oby[0x10]['src']==3 and oby[0x10]['displacement']==-2328, 'original R3 spill')
    need(oby[0x610]['opcode']==0x79 and oby[0x610]['dst']==8 and oby[0x610]['displacement']==-2328 and oby[0x618]['opcode']==0x57 and oby[0x618]['immediate']==1, 'original holder projection')
    for slot in range(-2328,-2320): need(oq(0x610,byte=slot)['definitions']==[0x10] and not oq(0x610,byte=slot)['entryWithoutDefinition'], 'original spill persistence')
    for pc in (0x640,0x720,0x1840): need(oq(pc,register=8)['definitions']==[0x618] and not oq(pc,register=8)['entryWithoutDefinition'], 'original true-use persistence')
    return {'status':'PASS_BOUNDED_H1_NEGATIVE_REPLAY','source':pins['source'],'raw':347,'normalized':1034,'total':1035,'raw_losses':687,'normalized_losses':0,'H1_body_bytes':26776,'original_body_bytes':27400,'prefix_instructions':len(rows),'H1_reaching_queries':len(queries),'original_reaching_queries':11,'validTagCallerEvaluation':valid_tags,'holder_result':mechanism['status'],'limits':'Conditional direct-FP/register evidence and finite valid-tag premise. Secondary39 receipt inspected, not independently rerun. No new official score, compiler, metric or VM; no source acceptance, original Rust-type inference or byte gain.'}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--native-zip',type=Path,required=True)
    parser.add_argument('--control-zip',type=Path,required=True)
    parser.add_argument('--capsule',type=Path,required=True)
    try: print(json.dumps(run(parser.parse_args()),indent=2))
    except Exception as error:
        print(json.dumps({'status':'FAIL_CLOSED','reason':str(error)}),file=sys.stderr)
        raise SystemExit(1)
