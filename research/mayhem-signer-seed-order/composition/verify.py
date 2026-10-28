"""Offline negative composition controls; no compiler, VM, Git or network use."""
if not __debug__:
    raise RuntimeError('Evidence checks require ordinary Python')
from pathlib import Path
from collections import Counter
import difflib,hashlib,importlib.util,io,json,tarfile,tempfile
HERE=Path(__file__).resolve().parent
LABELS=('baseline','baseline-repeat','late-inline','late-inline-repeat','late-staged','late-literal','price-eager','price-eager-inline')
EXPECT={'baseline':(12864,2368,599,50),'baseline-repeat':(12864,2368,599,50),'late-inline':(12848,6136,954,45),'late-inline-repeat':(12848,6136,954,45),'late-staged':(12640,6168,366,45),'late-literal':(12800,6152,752,45),'price-eager':(12864,2368,599,50),'price-eager-inline':(12848,6136,954,45)}

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def unpack(v,data):
    out={}
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:*') as tf:
        for member in tf.getmembers():
            name=v.safe(member.name);v.require(member.isfile() and name not in out,'composition archive member differs');out[name]=tf.extractfile(member).read()
    return out

def sources(root,v):
    acq=v.read(root/'acquisition.json');up=root/'upstream';pins=v.read(up/'source-inputs.json');manifest=v.read(up/'manifest.json')
    v.require(acq['revision']=='ea2b4e13db1c4e3d81836a4bdacbf312697d74d1','composition revision differs')
    v.require(v.identity((up/'manifest.json').read_bytes())['sha256']=='26d7a82681fe2c9e458f150e4d83592ba558b6c2c55f622059f55dec0e2a643b','upstream manifest identity differs')
    for name,pin in acq['files'].items():
        b=(up/v.safe(name)).read_bytes();v.require(v.identity(b)=={k:pin[k] for k in ('bytes','sha256')} and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==pin['git_blob'],'upstream Git blob differs')
        if name!='manifest.json':v.require(v.identity(b)['sha256']==manifest[name],'upstream file manifest differs')
    base=unpack(v,(up/'source.tar.xz').read_bytes());parent=v.read(root.parent/'source-inputs.json')
    v.require(len(base)==67 and {n:v.identity(b)['sha256'] for n,b in base.items()}==pins['parent']==parent==acq['parent_inputs'],'composition parent source differs')
    expected={'src/instructions/buy_v2.rs','src/instructions/pump_interface.rs','src/state.rs'}
    v.require(set(acq['changed_source_files'])==expected,'upstream source scope differs')
    for name in expected:base[name]=v.raw(up/'builds/proposed/overrides'/(name+'.gz'))
    v.require({n:v.identity(b)['sha256'] for n,b in base.items()}==pins['proposed']==acq['source_inputs'],'merged composition source differs')
    return base

def variant(root,v,base,label):
    v.require(label in LABELS,'unknown composition source');out=dict(base);name='src/instructions/pump_interface.rs';original=base[name];b=original
    def region(data):
        start=data.index(b'pub fn legacy_sell_handler(');a=data.index(b' let before_sol=',start);z=data.index(b' a.mayhem_token_vault.reload()?;a.bonding_curve.reload()?;',a);return a,z
    seed_label='late-inline' if label in ('late-inline','late-inline-repeat','price-eager-inline') else label if label in ('late-staged','late-literal') else None
    if seed_label:
        source=(root.parent/'source'/(seed_label+'.rs')).read_bytes();a,z=region(b);c,d=region(source);b=b[:a]+source[c:d]+b[z:]
    if label.startswith('price-eager'):
        old=b'  let scaled=reference.checked_mul(tolerance_bps as u128);';new=b'  let scaled=reference.checked_mul(tolerance_bps as u128).ok_or(MayhemError::MathOverflow)?;'
        v.require(b.count(old)==1,'price conversion control differs');b=b.replace(old,new)
        old=b'  let delta=scaled.ok_or(MayhemError::MathOverflow)?/10_000;';v.require(b.count(old)==1,'price quotient control differs');b=b.replace(old,b'  let delta=scaled/10_000;')
    def origin(data):i=data.index(b'error!(MayhemError::PumpCpiFailed)');return data[:i].count(b'\n')+1,i-data.rfind(b'\n',0,i)
    v.require(origin(b)==origin(original) and b.count(b'\n')==original.count(b'\n'),'composition source origin changed')
    if not label.startswith('baseline'):v.require((root/'sources'/(label+'.rs')).read_bytes()==b,'composition source transform differs')
    out[name]=b;return out

def calls(v,w,targets):
    v.require(all(c['target'] in targets for c in w['direct']),'composition call target lacks complete window')
    result=[(c['offset'],('local',*v.shape(targets[c['target']]))) for c in w['direct']]
    result += [(c['offset'],('import',c['relocation']['symbol'])) for c in w['external']]
    v.require(not w['indirect'] and not w['unrecognized_calls'],'unexpected handler call encoding');return sorted(result)

def body(v,e,originals,entry,tag):
    fs=v.functions(e);symbols=[s for s in e.symbols if s['info']&15==2 and '9__private8__global'+str(len(entry))+entry+'17h' in s['name']];v.require(len(symbols)==1,'unique entry wrapper required')
    wrapper=fs[symbols[0]['value']];old=[w for w in originals.values() if v.shape(w)==v.shape(wrapper)];v.require(len(old)==1,'entry wrapper shape differs');old=old[0]
    positions=[c['offset'] for c in old['direct'] if c['target']==originals[tag]['start']];v.require(len(positions)==1,'original entry call differs')
    targets=[c['target'] for c in wrapper['direct'] if c['offset']==positions[0]];v.require(len(targets)==1 and targets[0] in fs,'candidate entry call differs')
    return fs[targets[0]],dict(original_wrapper=old['start'],candidate_wrapper=wrapper['start'],call_offset=positions[0],target=targets[0])

def measure(v,e,original,originals):
    fs=v.functions(e);ot={w['start']:w for w in originals.values()};inv=v.inventory(e,originals);positive=v.positive_calls(originals,e,inv)
    result=dict(artifact=v.identity(e.b),inventory=inv,positive_internal_calls=positive,positive_internal_call_count=sum(map(len,positive.values())),handlers={})
    for entry,tag in [('buy','O0081'),('sell','O0082'),('buy_v2','O0083'),('sell_v2','O0084')]:
        cw,binding=body(v,e,originals,entry,tag);ow=originals[tag];oc=calls(v,ow,ot);cc=calls(v,cw,fs);oi=[c[1] for c in oc];ci=[c[1] for c in cc]
        a,_=original.norm(ow['start'],ow['end']);b,_=e.norm(cw['start'],cw['end']);seq=difflib.SequenceMatcher(None,[a[i:i+8] for i in range(0,len(a),8)],[b[i:i+8] for i in range(0,len(b),8)],autojunk=False);callseq=difflib.SequenceMatcher(None,oi,ci,autojunk=False)
        row=dict(binding=binding,start=cw['start'],bytes=cw['end']-cw['start'],original_bytes=ow['end']-ow['start'],raw_sha256=cw['raw_sha256'],normalized_sha256=cw['normalized_sha256'],normalization_pattern=cw['normalization_pattern'],complete_shape_equal=v.shape(ow)==v.shape(cw),diagnostic_aligned_slots=sum(m.size for m in seq.get_matching_blocks()),callee_multiset_equal=Counter(oi)==Counter(ci),ordered_callees_equal=oi==ci,ordered_matches=sum(m.size for m in callseq.get_matching_blocks()),original_calls=oc,candidate_calls=cc,call_alignment=[list(x) for x in callseq.get_opcodes()])
        if tag=='O0082':row['bump_read']=v.bump_read(e,cw);row['increment_patterns_before_bump']=v.increment_patterns(e,cw,row['bump_read']['offset'])
        result['handlers'][tag]=row
    return result

def verify(root=HERE,check_manifest=True):
    v=module('composition_parent_verifier',root.parent/'verify.py')
    if check_manifest:v.manifest_check(root.parent)
    base=sources(root,v);builds=v.read(root/'builds.json');v.require(set(builds)==set(LABELS),'composition build cohort differs')
    reader=module('composition_unchanged_reader',root.parent/'reader.py');v.require(v.identity((root.parent/'reader.py').read_bytes())['sha256']==v.read(root.parent/'scope.json')['reader_sha256'],'composition reader changed')
    rows=v.read(root.parent/'reference/original-windows.json');images={};results={}
    def equivalent(a,b):return all(a[k]==b[k] for k in ('bytes','normalized_sha256','normalization_pattern','candidate_calls'))
    with tempfile.TemporaryDirectory(prefix='mayhem-signer-composition-') as tmp:
        def elf(name,data):p=Path(tmp)/name;p.write_bytes(data);return reader.Elf(p)
        original=elf('original.so',v.raw(root.parent/'reference/original.so.gz'));v.require(v.identity(original.b)['sha256']==v.ORIGINAL,'original capture changed');originals={r['id']:original.window(r['start'],r['end']) for r in rows}
        upstream=elf('upstream.so',v.raw(root/'upstream/builds/proposed/symbols.so.gz'));v.require(v.identity(upstream.b)['sha256']=='7e317f633be8605eed4eedc905e3d7a95edd1a51d635ed2c49503f46ecdfded0','upstream ELF changed');up=measure(v,upstream,original,originals)
        for label in LABELS:
            folder=root/'builds'/label;launch=v.read(folder/'launch.json.gz');receipt=v.read(folder/'result.json.gz');record=builds[label];inputs=variant(root,v,base,label)
            v.require({n:v.identity(b)['sha256'] for n,b in inputs.items()}==launch['source_inputs']==record['source_inputs'],'composition build source binding differs')
            v.require(launch['parent_source_inputs']=={n:v.identity(b)['sha256'] for n,b in base.items()},'composition launch parent differs')
            v.require(receipt['status']=='SUCCEEDED' and receipt['returncode']==0 and receipt['target_executions']==0 and receipt['source_unchanged'] and receipt['dependencies_unchanged'] and receipt['strip']['returncode']==0,'composition build failed/unexecuted')
            images[label]={n:v.raw(folder/(n+'.gz')) for n in record['outputs']}
            v.require({n:v.identity(b) for n,b in images[label].items()}==record['outputs']==receipt['outputs'],'composition complete output binding differs')
            e=elf(label+'.so',images[label]['symbols.so']);strip=elf(label+'-strip.so',images[label]['candidate-v154-strip.so']);v.require(v.allocated(e)==v.allocated(strip),'composition strip changed allocated sections')
            row=measure(v,e,original,originals);results[label]=row;inv=row['inventory'];v.require((inv['normalized'],inv['raw_local'],inv['injective'])==(432,77,431),'composition native inventory changed')
            h=row['handlers']['O0082'];v.require((h['bytes'],h['bump_read']['offset'],h['diagnostic_aligned_slots'],h['ordered_matches'])==EXPECT[label],'composition measured diagnostic differs')
            v.require(all(not h['complete_shape_equal'] and h['callee_multiset_equal'] for h in row['handlers'].values()),'composition whole body/callee scope changed')
            if label=='baseline':
                baseline=row;first=launch
                v.require(all(equivalent(h,up['handlers'][tag]) for tag,h in row['handlers'].items()),'native baseline fails to reproduce upstream handler shapes/calls')
            else:
                bi=baseline['inventory'];v.require(inv['raw_ids']==bi['raw_ids'] and {k for k,a in inv['matches'].items() if a}=={k for k,a in bi['matches'].items() if a},'composition match set changed')
                v.require(row['positive_internal_calls']==baseline['positive_internal_calls'],'composition positive internal call set changed')
                v.require(all(equivalent(row['handlers'][tag],baseline['handlers'][tag]) for tag in ('O0081','O0083','O0084')),'composition changed another handler')
                v.require(launch['checked_executables']==first['checked_executables'] and launch['reused_dependencies']==first['reused_dependencies'] and launch['root_record']==first['root_record'],'composition compiler/dependency context changed')
            v.require(e.b!=original.b and strip.b!=original.b,'unexpected original whole equality')
        for a,b in [('baseline','baseline-repeat'),('late-inline','late-inline-repeat'),('baseline','price-eager'),('late-inline','price-eager-inline')]:v.require(images[a]==images[b],'composition complete repeat/price-control equality differs')
    v.require(results['baseline']['positive_internal_call_count']==4314,'composition internal observation count differs')
    fresh=root/'rebuild-validation';receipt=v.read(fresh/'result.json.gz');comparison=v.read(fresh/'comparison.json.gz');launch=v.read(fresh/'launch.json.gz')
    v.require(receipt['status']=='SUCCEEDED' and receipt['returncode']==0 and receipt['source_unchanged'] and receipt['root_invocations']==1 and receipt['target_executions']==0,'fresh composition rebuild incomplete')
    v.require(comparison['outputs_equal'] and comparison['variant']=='late-inline' and comparison['actual']==comparison['expected']==receipt['outputs']==builds['late-inline']['outputs'],'fresh composition outputs differ')
    v.require(launch['target_directory_initially_absent'] and launch['source_inputs']==builds['late-inline']['source_inputs'],'fresh composition source binding differs')
    v.require(launch['checked_executables']==first['checked_executables'],'fresh composition tools differ')
    for name,pin in receipt['logs'].items():v.require(v.identity(v.raw(fresh/(name+'.gz')))==pin,'fresh composition log differs')
    records=[json.loads(b) for b in v.unpack((fresh/'wrapper-records.tar.gz').read_bytes()).values()]
    commands=[c for c in records if '--crate-name' in c['after'] and any(a in c['after'] for a in ('--emit=dep-info,link','--emit=dep-info,metadata,link'))]
    targets=[c for c in commands if '--target' in c['after'] and c['after'][c['after'].index('--target')+1]=='sbpf-solana-solana']
    v.require(len(commands)==163 and len(targets)==85,'fresh composition compiler cohort differs')
    metadata=[line.split('\t') for line in (root.parent/'controller/metadata-map.tsv').read_text().splitlines()]
    for command in targets:
        before=[a[9:] for a in command['before'] if a.startswith('metadata=')];after=[a[9:] for a in command['after'] if a.startswith('metadata=')];name=command['after'][command['after'].index('--crate-name')+1]
        v.require(len(before)==len(after)==1 and [before[0],after[0],name] in metadata,'fresh composition metadata binding differs')
    placement=module('composition_placement_reader',root/'placement/verify.py').verify(root/'placement',False)
    v.require(placement==v.read(root/'placement/report.json.gz'),'placement saved report differs')
    arithmetic=module('composition_arithmetic_reader',root/'arithmetic/verify.py').verify(root/'arithmetic',False)
    v.require(arithmetic==v.read(root/'arithmetic/report.json.gz'),'arithmetic saved report differs')
    return json.loads(json.dumps(dict(upstream=up,builds=results,compiler_builds=9,incremental_root_builds=8,fresh_dependency_builds=1,rebuild_compiler_commands=163,placement_diagnostics=dict(compiler_builds=4,pre_placement_callees_equal=True,post_placement_callees_equal=False,post_placement_matches_both_final_artifacts=True),complete_windows_gained=0,target_executions=0,whole_original_equal=False,scope='Negative source controls. Internal observations exclude imported calls. Alignment and call-order correspondence are file-layout diagnostics, not recovery, dynamic call order or runtime qualification.')))

if __name__=='__main__':
    r=verify();v=module('composition_report_reader',HERE.parent/'verify.py');v.require(r==v.read(HERE/'report.json.gz'),'composition saved report differs');print('Verified eight root builds and one fresh full rebuild: all late-seed forms regress ordered callees; all original handler bodies remain unmatched.')
