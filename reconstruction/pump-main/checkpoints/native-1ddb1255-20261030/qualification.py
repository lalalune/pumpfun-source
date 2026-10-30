"""Source/build admission primitives adapted from accepted checkpoint2232 and sealed c086.

The official scorer is read byte-for-byte from explicit frozen Git objects;
none of its functions or rules are replaced. Git reads prohibit lazy fetch.
"""
import ast,csv,hashlib,importlib.util,io,json,os,re,subprocess,sys,tarfile,zipfile
from pathlib import Path,PurePosixPath
HEAD=None
FROZEN_FILES={}
SCORER_PATHS=()
ORIGINAL='7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
INPUT_PATHS=('reconstruction/harness/score.py','reconstruction/harness/llvm_tools.py','reconstruction/harness/elf_symbols.py','reconstruction/base/functions.tsv','reconstruction/pump-main/baseline/score.json','reconstruction/pump-main/baseline/rescore.json')
CORE=('reconstruction/harness','reconstruction/toolchain','reconstruction/base','reconstruction/pump-main/baseline','evidence/original/pump')

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    # Duplicate JSON keys must not silently select one provenance assertion.
    def unique(pairs):
        out = {}
        for key, value in pairs:
            need(key not in out, f'duplicate JSON key: {key}')
            out[key] = value
        return out
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique)

def git(repo, *args):
    env = dict(os.environ, GIT_NO_LAZY_FETCH='1')
    return subprocess.check_output(['git', '--no-lazy-fetch', '-c', 'gc.auto=0', '-c',
        'maintenance.auto=false', '-C', str(repo), *args], env=env)

def git_file(repo, head, path):
    data = git(repo, 'show', f'{head}:{path}')
    expected = git(repo, 'rev-parse', f'{head}:{path}').decode().strip()
    need(blob_id(data) == expected, f'Git blob bytes differ: {path}')
    return data

def blob_id(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def source_tree(repo):
    out = {}
    for line in git(repo, 'ls-tree', '-r', HEAD, 'programs/pump').decode().splitlines():
        meta, path = line.split('\t')
        mode, kind, blob = meta.split()
        need(kind == 'blob' and mode == '100644', f'unsupported source entry: {path}')
        data = git(repo, 'cat-file', 'blob', blob)
        out[path] = {'mode': mode, 'gitBlob': blob, 'sha256': sha(data),
                     'bytes': len(data), 'data': data}
    need(bool(out), 'empty standalone source inventory')
    return out

def frozen_inputs(repo, original):
    need(git(repo, 'rev-parse', HEAD).decode().strip() == HEAD, 'missing exact source commit')
    need(git(repo, 'cat-file', '-t', HEAD).strip() == b'commit', 'source pin is not a commit')
    bindings = {}
    for path in INPUT_PATHS:
        data = git_file(repo, HEAD, path)
        digest = sha(data)
        FROZEN_FILES[path] = data
        bindings[path] = {'sha256': digest, 'gitBlob': blob_id(data)}
    ob = original.read_bytes()
    need(sha(ob) == ORIGINAL, 'captured original ELF hash differs')
    source = source_tree(repo)
    baseline = json.loads(FROZEN_FILES['reconstruction/pump-main/baseline/score.json'])['windows']
    rescore = json.loads(FROZEN_FILES['reconstruction/pump-main/baseline/rescore.json'])
    rows = [r for r in csv.DictReader(io.StringIO(FROZEN_FILES['reconstruction/base/functions.tsv'].decode()), delimiter='\t')
            if r['program'] == 'pump' and r['variant'] == 'selected']
    expected = {int(r['original_start']): int(r['bytes']) for r in rows}
    need(len(rows) == len(expected) == 1035, 'original inventory is not 1035 unique windows')
    for other in (baseline, rescore['windows']):
        need(set(map(int, other)) == set(expected), 'baseline window membership differs')
        for key, row in other.items():
            need(type(row['normalized']) is bool and type(row['raw']) is bool,
                 'non-boolean baseline membership')
            need(row['bytes'] == expected[int(key)] and (not row['raw'] or row['normalized']),
                 'invalid baseline length/raw membership')
    for key in baseline:
        need(all(baseline[key][field] == rescore['windows'][key][field]
                 for field in ('normalized', 'raw', 'bytes')), 'frozen baseline and rescore disagree')
    historical = {'label': 'frozen Git baseline/rescore reference, NOT the incoming source build',
        'symbols_sha256': rescore['summary']['candidate_sha256'],
        'normalized': sum(r['normalized'] for r in baseline.values()),
        'raw': sum(r['raw'] for r in baseline.values()), 'total': len(baseline)}
    need(historical['normalized'] == rescore['summary']['normalized'] and historical['raw'] == rescore['summary']['raw'], 'historical counts differ from bound rescore')
    return source, baseline, expected, bindings, historical, ob

def load_scorer(repo, original, output):
    # Exact maintained code in an isolated input projection. No monkeypatch of
    # scorer globals or functions: BASE resolves normally to authenticated links.
    replay = output / 'scorer-replay/reconstruction'
    harness, base = replay / 'harness', replay / 'base'
    harness.mkdir(parents=True)
    base.mkdir()
    for relative in SCORER_PATHS:
        data = FROZEN_FILES[relative]
        dst = harness / Path(relative).name
        dst.write_bytes(data)
        need(sha(dst.read_bytes()) == sha(data), 'current scorer projection differs')
    (base / 'original.so').symlink_to(original.resolve())
    (base / 'functions.tsv').write_bytes(FROZEN_FILES['reconstruction/base/functions.tsv'])
    path = harness / 'score.py'
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location('maintained_pump_score', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def discover_scorer_paths(repo):
    """Exact in-harness import closure, including function-local imports."""
    available = {line.split('\t', 1)[1] for line in
        git(repo, 'ls-tree', '-r', HEAD, 'reconstruction/harness').decode().splitlines()}
    pending = ['reconstruction/harness/score.py']
    found = set()
    while pending:
        relative = pending.pop()
        if relative in found:
            continue
        data = git_file(repo, HEAD, relative)
        found.add(relative)
        for node in ast.walk(ast.parse(data)):
            names = [node.module] if isinstance(node, ast.ImportFrom) and node.module else (
                [alias.name for alias in node.names] if isinstance(node, ast.Import) else [])
            for name in names:
                target = 'reconstruction/harness/' + name.replace('.', '/') + '.py'
                if target in available and target not in found:
                    pending.append(target)
    need('reconstruction/harness/elf_symbols.py' in found, 'current internal ELF parser not in scorer closure')
    return tuple(sorted(found))

def emit(root,name,value):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as out:json.dump(value,out,sort_keys=True,indent=2);out.write('\n')

def rows(repo,head,prefixes):
    result=[]
    for item in git(repo,'ls-tree','-rz',head,'--',*prefixes).split(b'\0'):
        if not item:continue
        meta,path=item.split(b'\t');mode,kind,oid=meta.decode().split();path=path.decode()
        need(kind=='blob' and mode in ('100644','100755','120000'),'unsupported Git member')
        data=git_file(repo,head,path)
        result.append({'path':path,'mode':mode,'gitBlob':oid,'bytes':len(data),'sha256':sha(data)})
    need(result,'empty Git vector');return result

def parent(repo,child,base):
    raw=git(repo,'cat-file','-p',child).split(b'\n\n',1)[0].splitlines()
    need([x[7:].decode() for x in raw if x.startswith(b'parent ')]==[base],'unexpected commit parents')

def outer(args):
    need(re.fullmatch('[0-9a-f]{64}',args.archive_sha256),'full API archive digest required')
    need(sha(args.archive.read_bytes())==args.archive_sha256,'outer artifact digest differs')
    observed={}
    with zipfile.ZipFile(args.archive) as z:
        for info in z.infolist():
            name=info.filename
            need(name and not name.startswith('/') and '\\' not in name and all(x not in ('','.','..') for x in name.split('/')),'unsafe ZIP member')
            need(not info.is_dir() and name not in observed and (info.external_attr>>16)&0o170000!=0o120000,'ZIP type/duplicate mismatch')
            data=z.read(info);p=args.artifact/name
            need(p.is_file() and not p.is_symlink() and p.read_bytes()==data,'ZIP/extracted member differs: '+name)
            observed[name]={'bytes':len(data),'sha256':sha(data)}
    actual={p.relative_to(args.artifact).as_posix() for p in args.artifact.rglob('*') if p.is_file()}
    need(actual==set(observed),'extracted artifact member set differs')
    emit(args.output,'OUTER-ARCHIVE.json',{'sha256':args.archive_sha256,'bytes':args.archive.stat().st_size,'members':observed})

def tar_check(path,expected,exact_modes=None):
    observed={}
    with tarfile.open(path,'r:gz') as archive:
        for member in archive:
            name=member.name
            need(member.isfile() and name in expected and name not in observed,'archive member/type/set differs')
            data=archive.extractfile(member).read();row=expected[name]
            need(len(data)==row['bytes'] and sha(data)==row['sha256'],'archive byte mismatch: '+name)
            need(bool(member.mode&0o111)==row.get('executable',False),'archive executable mode differs')
            if exact_modes:need(member.mode&0o7777==int(exact_modes[name],8)&0o7777,'source archive mode differs')
            observed[name]={'bytes':len(data),'sha256':sha(data),'mode':oct(member.mode)}
    need(set(observed)==set(expected),'archive source set differs');return observed

def snapshot(source):
    files=sorted([{'path':p.removeprefix('programs/pump/'),'bytes':v['bytes'],'sha256':v['sha256'],'executable':bool(int(v['mode'],8)&0o111)} for p,v in source.items()],key=lambda r:r['path'])
    return {'schema':'pump-source-inputs-v1','files':files,'sha256':sha(json.dumps(files,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())}

def summary(windows,baseline,digest):
    result={'candidate_sha256':digest,'normalized':sum(r['normalized'] for r in windows.values()),'raw':sum(r['raw'] for r in windows.values()),'total':len(windows),'matched_text_bytes':sum(r['bytes'] for r in windows.values() if r['normalized'])}
    for flag,plus,minus in [('normalized','gains','losses'),('raw','raw_gains','raw_losses')]:
        result[plus]=[hex(k) for k in sorted(windows) if windows[k][flag] and not baseline[k][flag]]
        result[minus]=[hex(k) for k in sorted(windows) if baseline[k][flag] and not windows[k][flag]]
    return result

def recorded_json(text):
    found=[]
    for match in re.finditer(r'(?m)^\{',text):
        try:value,_=json.JSONDecoder().raw_decode(text[match.start():])
        except json.JSONDecodeError:continue
        if isinstance(value,dict) and 'unstripped_sha256' in value:found.append(value)
    need(len(found)==1,'actual cold builder result absent/ambiguous');return found[0]

def link_check(args,label,source,build,native_lld,core):
    folder=args.artifact/label;record=read_json(folder/'link-inputs.json');program=source['programs/pump/link/ordered.ld'];maintained={Path(r['path']).name:r for r in core if r['path'] in ['reconstruction/harness/'+name for name in ('link_order.py','pump_link_rustc.py','pump_link_lld.py','sbf_default.ld')]}
    need({k:record['programScript'][k] for k in ('mode','gitBlob','bytes','sha256')}=={k:program[k] for k in ('mode','gitBlob','bytes','sha256')},'frozen linker script provenance differs')
    need(record['maintainedInputs']==maintained,'link helper/default Git vector differs')
    for name,row in maintained.items():need(sha((folder/'pinned-link-inputs'/name).read_bytes())==row['sha256'],'retained link helper differs')
    need((folder/'pinned-link-inputs/ordered.ld').read_bytes()==program['data'],'retained program link script differs')
    # Import only frozen maintained pure checker, never configure() or a linker.
    module_path=args.output/'maintained-link-order.py';module_path.write_bytes(git_file(args.repo,args.source_base,'reconstruction/harness/link_order.py'))
    spec=importlib.util.spec_from_file_location('maintained_link_admission',module_path);link=importlib.util.module_from_spec(spec);spec.loader.exec_module(link)
    counts=link.check_script(program['data'].decode(),git_file(args.repo,args.source_base,'reconstruction/harness/sbf_default.ld').decode())
    need(record['selectors']==counts and record['stagedScriptSha256']==program['sha256'] and record['configureExecutedByPreflight'] is False,'link preflight record differs')
    expected={'script':'link/ordered.ld','script_sha256':program['sha256'],'selectors':counts,'lld_sha256':native_lld['sha256']}
    need(build.get('link_order')==expected,'actual build.link_order differs')
    actual=read_json(folder/'link-receipt.json');cold=read_json(folder/'cold-target-inputs.json');work=PurePosixPath(cold['target']).parent;script=str(work/'ws/programs/pump/link/ordered.ld')
    need(actual['script']==script and actual['script_sha256']==program['sha256'] and actual['default_script_sha256']==maintained['sbf_default.ld']['sha256'] and actual['lld']==native_lld['path'] and actual['lld_sha256']==native_lld['sha256'],'actual link receipt binding differs')
    argv=actual['forwarded'];need([argv[i+1] for i,v in enumerate(argv[:-1]) if v in ('-T','--script')]==[script] and argv.count('-Map='+str(work/'link.map'))==1,'forwarded script/map differs')
    linkmap=folder/'link.map';need(linkmap.is_file() and linkmap.stat().st_size>0,'actual link map missing')
    admission=read_json(folder/'link-order-admission.json')
    need(admission['actualBuildLinkOrder']==expected and admission['receiptSha256']==sha((folder/'link-receipt.json').read_bytes()) and admission['mapSha256']==sha(linkmap.read_bytes()) and admission['mapBytes']==linkmap.stat().st_size and admission['nativeLld']==native_lld and admission['frozenProgramScript']==record['programScript'] and admission['frozenDefaultScript']==maintained['sbf_default.ld'],'recorded link admission differs')
    return {'scriptSha256':program['sha256'],'defaultSha256':maintained['sbf_default.ld']['sha256'],'selectors':counts,'nativeLldSha256':native_lld['sha256'],'mapSha256':sha(linkmap.read_bytes())}
