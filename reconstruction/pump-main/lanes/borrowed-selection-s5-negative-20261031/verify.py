"""Bounded S5 borrowed-key negative replay. Reads fixed captures; never runs project code."""
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
def capsule_members(data, source, operational):
    members = tar_members(data); get = lambda name: members[name][0]
    manifest = js(get('CAPSULE-MANIFEST.json'))
    need(set(members) == set(manifest['files']) | {'CAPSULE-MANIFEST.json'}, 'capsule domain')
    need(manifest['source'] == source and manifest['operational'] == operational, 'capsule source cohort')
    for name, row in manifest['files'].items():
        need(len(get(name)) == row['bytes'] and sha(get(name)) == row['sha256'], 'capsule '+name)
    return get

def actual_prefix(native, capsule, stem, expected):
    sections, symbols = elf(native['unstripped.so']); text = sections['.text']
    matches = [s for s in symbols if 'admin_cto7execute17h' in s['name']]
    need(len(matches) == 1, 'unique execute')
    symbol = matches[0]; start = text[4]+symbol['address']-text[3]
    body = native['unstripped.so'][start:start+symbol['bytes']]
    need(symbol['address'] == 0x22a10 and len(body) == symbol['bytes'] == expected['bodyBytes'] and sha(body) == expected['bodySHA256'], 'actual execute extent/body')
    cache = js(capsule('work/native-inspection/actual/'+stem+'-PREFIX.json'))
    end = cache['prefix']['bytes']; rows = decode(body[:end],symbol['address'],symbols)
    need(rows == cache['rows'] and sha(body[:end]) == expected['prefixSHA256'], 'raw bounded prefix replay')
    need('prepare_bonding_curve' in (rows[-1].get('callName') or '') and not any('prepare_bonding_curve' in (r.get('callName') or '') for r in rows[:-1]), 'first actual named prepare boundary')
    need(not cache['scopedOutlineCallsInPrefix'], 'no outlined mechanism callee traversed')
    return reaching(rows), rows

def run(args):
    pins = js((HERE/'inputs.json').read_bytes())
    native = zip_members(pinned(args.native_zip,pins['inputs']['nativeZip']))
    control = zip_members(pinned(args.control_zip,pins['inputs']['controlZip']))
    c = capsule_members(pinned(args.capsule,pins['inputs']['capsule']),pins['source'],pins['operational'])
    d = capsule_members(pinned(args.control_capsule,pins['inputs']['controlCapsule']),pins['parent'],pins['referenceOperational'])
    for members, image_pins in ((native,pins['images']),(control,pins['referenceImages'])):
        for name, value in image_pins.items(): need(sha(members[name]) == value, 'actual image '+name)
    src, old = js(native['program-source-inputs.json']), js(control['program-source-inputs.json'])
    a,b = ({r['path']:r for r in value['files']} for value in (src,old)); leaf = 'programs/pump/src/creator/admin_cto.rs'
    need(src['base'] == pins['source'] and old['base'] == pins['parent'] and len(a) == len(b) == 263 and set(a) == set(b), 'source263 domains')
    need([name for name in a if a[name] != b[name]] == [leaf], 'sole changed source leaf')
    need(js(native['toolchain-source-inputs.json'])['files'] == js(control['toolchain-source-inputs.json'])['files'] and len(js(native['toolchain-source-inputs.json'])['files']) == 279, 'CORE279 unchanged')
    for members,index in ((native,a),(control,b)):
        archive = tar_members(members['program-source.tar.gz']); need(set(archive) == set(index), 'source TAR domain')
        for name,row in index.items():
            value, executable = archive[name]
            need(len(value) == row['bytes'] and sha(value) == row['sha256'] and executable == (row['mode'] == '100755') and hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest() == row['gitBlob'], 'typed source TAR '+name)
        selected = js(members['source-inputs.json']); stage = js(members['compiled-workspace-inputs.json'])
        need(len(selected['files']) == 263 and len(stage) == 264 and sha(json.dumps(selected['files'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()) == selected['sha256'], 'selected263/stage264')
        staged = tar_members(members['compiled-workspace.tar.gz']); need(set(staged) == set(stage), 'staged archive domain')
        for name,row in stage.items():
            value, executable = staged[name]
            need(len(value) == row['bytes'] and sha(value) == row['sha256'] and executable == row['executable'], 'staged member '+name)
    before = tar_members(control['program-source.tar.gz'])[leaf][0]; after = tar_members(native['program-source.tar.gz'])[leaf][0]
    need(after == c('source/admin_cto.rs') and before == c('source/parent-admin_cto.rs'), 'actual compiled source leaves')
    aa,bb = before.splitlines(keepends=True),after.splitlines(keepends=True)
    need(len(aa) == len(bb) == 772 and [i+1 for i,(x,y) in enumerate(zip(aa,bb)) if x!=y] == [283,298,307,312,339], 'five changed source lines')
    need(aa[313:338] == bb[313:338] and aa[339:] == bb[339:], 'fees and downstream source unchanged')
    need(b"Result<&'a Pubkey>" in bb[282] and b'if shared{&st.creator}else{t}' in bb[311] and b'let target=*validate(&st,hopt,fee,&new,&holder_key,&sk,shared)?;' in bb[338], 'borrowed selection source, not original ABI evidence')
    need((HERE/'SOURCE.patch').read_bytes() == c('work/native-prep/S5-SOURCE.patch'), 'exact retained source patch')
    public = js(c('work/native-run/PUBLIC-SOURCE.json'))
    need(public['sha'] == pins['source'] and public['commit']['tree']['sha'] == pins['sourceTree'] and [p['sha'] for p in public['parents']] == [pins['parent']] and len(public['files']) == 1 and public['files'][0]['sha'] == a[leaf]['gitBlob'], 'genuine public source checkpoint metadata')
    report = js(c('work/root/CURRENT-ELF-ADMISSION.json')); official_bytes = c('work/root/admission/official-score/score.json'); official = js(official_bytes)
    windows, reference = official['windows'], js(control['score.json'])['windows']
    need(windows == js(native['score.json'])['windows'] and len(windows) == len(reference) == 1035 and set(windows) == set(reference), 'all1035 official/native/reference score rows')
    losses = {kind:[hex(int(k)) for k in sorted(windows,key=int) if reference[k][kind] and not windows[k][kind]] for kind in ('raw','normalized')}
    gains = {kind:[hex(int(k)) for k in sorted(windows,key=int) if windows[k][kind] and not reference[k][kind]] for kind in ('raw','normalized')}
    need(sum(r['raw'] for r in reference.values()) == sum(r['normalized'] for r in reference.values()) == 1034, 'actual D421 control1034')
    need(sum(r['raw'] for r in windows.values()) == 347 and sum(r['normalized'] for r in windows.values()) == 1034 and len(losses['raw']) == 687 and not losses['normalized'] and not gains['raw'] and not gains['normalized'], 'rejection arithmetic')
    need(report['comparison']['rawLosses'] == losses['raw'] and report['comparison']['normalizedLosses'] == [] and report['membershipQualification'] == 'REJECTED_RAW_OR_NORMALIZED_LOSS' and report['sourceAndNativeProvenanceConclusion'] == 'PASS' and report['officialScore']['jsonSha256'] == sha(official_bytes), 'recorded actual rejection')
    for capsule in (c,d):
        secondary = js(capsule('work/secondary-admission-reader/actual-review/REVIEW.json'))
        need(len(secondary['checks']) == 39 and all(x['pass'] for x in secondary['checks']), 'retained secondary39; not independently rerun')
    (by,query),rows = actual_prefix(native,c,'S5',pins['candidateCTO'])
    (db,dq),drows = actual_prefix(control,d,'D421',pins['referenceCTO'])
    mechanism = js(c('work/native-inspection/actual/S5-MECHANISM.json'))
    need(len(mechanism['queries']) == mechanism['queryCount'] == 113, 'S5 query domain')
    for q in mechanism['queries']: need(query(q['at'],q.get('register'),q.get('fpByte')) == q, 'S5 reaching '+str(q))
    need(query(0x1348,register=7)['definitions'] == [0x1340] and query(0x1358,register=6)['definitions'] == [0xb30], 'C-snapshot/N-payload pointer alternatives')
    need(by[0x1338]['opcode'] == 0xbf and by[0x1338]['src'] == 10 and by[0x1340]['opcode'] == 0x07 and by[0x1340]['immediate'] == -48 and by[0x1350]['jump'] == 0x1360 and by[0x1358]['opcode'] == 0xbf and by[0x1358]['dst'] == 7 and by[0x1358]['src'] == 6, 'exact conditional selected-pointer instruction chain')
    fee_loads = [r for r in rows if r.get('memoryKind') == 'read' and r.get('memoryBase') == 10 and r['displacement'] == -2312]
    need(fee_loads == mechanism['feeTagDirectLoads'] and [r['offset'] for r in fee_loads] == [0xa18,0x1360], 'only two saved incoming fee-tag loads in prefix')
    need(query(0x1460,register=7)['definitions'] == query(0x1638,register=7)['definitions'] == [0xa30,0x1340,0x1358] and query(0x1648,register=7)['definitions'] == [0x1340,0x1358], 'selected pointer survives to fee/None paths')
    writes = [r for r in rows if r.get('memoryKind') == 'write' and r.get('memoryBase') == 10 and r['displacement'] < -1592 and r['displacement']+r['memoryWidth'] > -1624]
    need(writes == mechanism['selectedTargetDirectWrites'] and [r['offset'] for r in writes] == [0x1650,0x1660,0x1670,0x1680,0x18a8,0x18b8,0x18c8,0x18d8,0x1998,0x19a8,0x19b8,0x19c8], 'complete direct selected-target write inventory')
    need(by[0x1370]['jump'] == 0x1648 and by[0xa20]['jump'] == 0x1990 and by[0x1640]['jump'] == 0x18a0, 'post-tag/fee-success materialization edges')
    need(by[0xc10]['jump'] == 0x1338 and all(by[p].get('callName') == 'memcmp' for p in (0xb78,0xbb8,0xbf8)), 'N guards precede conditional target-pointer choice')
    for name,rr in mechanism['ranges'].items(): need(all(by[r['offset']] == r for r in rr), 'bound actual range '+name)
    old_mechanism = js(d('work/native-inspection/actual/CURRENT-LATE-C.json'))
    old_queries = old_mechanism['pointerQueries']+old_mechanism['curvePointerSavedByteQueries']
    for q in old_queries:
        expected = {'at':q['at'],'definitions':q['definitions'],'entryWithoutDefinition':q['entry'],**({'register':q['register']} if 'register' in q else {'fpByte':q['byte']})}
        need(dq(q['at'],q.get('register'),q.get('byte')) == expected, 'D421 direct provenance query')
    for name in ('commonKeyWrites','COverwrite','NToSeparateScratch','outerSelectedKeyPieces','outerSharingScratchCopy'):
        need(all(db[r['offset']] == r for r in old_mechanism[name]), 'D421 baseline range '+name)
    path = old_mechanism['chosenSharedNonholderPath']; need(all(p in db for p in path), 'D421 chosen-path domain')
    for p,q in zip(path,path[1:]):
        r = db[p]; edges = [r['jump']]+([p+r['bytes']] if r['opcode']&0xf0 else []) if 'jump' in r else [p+r['bytes']]
        need(q in edges, 'actual selected path edge')
    stop = min(r['offset'] for r in old_mechanism['COverwrite'])
    ranges = [(-1624,-1617),(-1328,-1319)]
    reads = [p for p in path if p<stop and db[p].get('memoryKind') == 'read' and db[p].get('memoryBase') == 10 and any(db[p]['displacement']<b and db[p]['displacement']+db[p]['memoryWidth']>a for a,b in ranges)]
    need(not reads and not any(db[p]['opcode'] in (0x85,0x8d) for p in path) and not old_mechanism['directKeyReadsBeforeCOverwrite'] and not old_mechanism['callsInSuffix'], 'bounded no-direct-use-before-C suffix; no arbitrary alias proof')
    original = pinned(args.repo/pins['original']['path'],pins['original']); os,unused = elf(original); text = os['.text']; start = text[4]+0x22a10-text[3]
    need(sha(original[start:start+27400]) == pins['original']['bodySHA256'], 'captured original body identity; not decoded or measured')
    return {'status':'PASS_BOUNDED_S5_BORROWED_SELECTION_NEGATIVE_REPLAY','source':pins['source'],'parent':pins['parent'],'sourceFiles':263,'COREfiles':279,'stageFiles':264,'officialRows':1035,'raw':347,'normalized':1034,'rawLosses':687,'normalizedLosses':0,'candidateCTObytes':26936,'controlCTObytes':27400,'candidateDirectQueries':113,'controlDirectQueries':len(old_queries),'selectedPointerBeforeFee':True,'selectedTargetStoresStillAfterTagOrFeeSuccess':True,'incomingSharingPayloadDistinct':True,'limits':'Read-only raw-prefix replay and direct FP/register facts, with exact source valid-value/role premises and opaque alias limits. Retained secondary39 receipts inspected, not independently rerun. Frozen D421 diagnostic, not latest-main source qualification or original private ABI inference. No official rescoring, compiler, token similarity metric, VM or source acceptance.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--native-zip',type=Path,required=True)
    parser.add_argument('--capsule',type=Path,required=True)
    parser.add_argument('--control-zip',type=Path,required=True)
    parser.add_argument('--control-capsule',type=Path,required=True)
    args = parser.parse_args()
    need(sys.dont_write_bytecode and sys.flags.optimize == 0, 'Use python3 -B without optimized assertions')
    print(json.dumps(run(args),indent=2))

if __name__ == '__main__': main()
