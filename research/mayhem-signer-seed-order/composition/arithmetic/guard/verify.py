"""Bind ordinary price-order and Option controls to actual compiler artifacts."""
if not __debug__:
    raise RuntimeError('Evidence checks require ordinary Python')
from pathlib import Path
import importlib.util,json,struct,tempfile
HERE=Path(__file__).resolve().parent
LABELS=('checked-price-first-late','option-projection-late','checked-price-first-late-repeat')
TRANSFORMS={
 'checked-price-first-late':(b'  let scaled=reference.checked_mul(tolerance_bps as u128);\n  let price=vs*1_000_000_000_000_000u128/vt;',b'  let price=vs*1_000_000_000_000_000u128/vt;\n  let scaled=reference.checked_mul(tolerance_bps as u128);'),
 'option-projection-late':(b'  let delta=if overflow{return Err(MayhemError::MathOverflow);}else{scaled}/10_000;',b'  let delta=(!overflow).then_some(scaled).ok_or(MayhemError::MathOverflow)?/10_000;')}

def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def variant(root,v,c,a,base,label):
    v.require(label in LABELS,'unknown guard source');label=label.removesuffix('-repeat')
    out=c.variant(root.parent.parent,v,base,'late-inline') if label.startswith('checked') else a.variant(root.parent,v,c,base,'overflow-late')
    name='src/instructions/pump_interface.rs';original=out[name];old,new=TRANSFORMS[label]
    v.require(original.count(old)==1,'guard source anchor differs');b=original.replace(old,new)
    v.require(b==(root/'sources'/(label+'.rs')).read_bytes(),'guard source transform differs')
    def origin(s):i=s.index(b'error!(MayhemError::PumpCpiFailed)');return s[:i].count(b'\n'),i-s.rfind(b'\n',0,i)
    v.require(b.count(b'\n')==original.count(b'\n') and origin(b)==origin(original),'guard source coordinates shifted');out[name]=b;return out

def witness(v,c,e,w,originals,label):
    checked=label.startswith('checked');off,opcode,target=(576,0x55,952) if checked else (560,0x15,936)
    def ins(at):return struct.unpack_from('<BBhi',e.b,w['start']+at)
    v.require(ins(off)==(0x57,7,0,1),'guard control low-bit mask differs')
    op,reg,delta,imm=ins(off+8);v.require((op,reg,imm)==(opcode,7,0) and off+16+delta*8==target,'guard control branch differs')
    if checked:
        v.require(ins(target)==(0xb7,7,0,2),'guard error tag differs')
        op,reg,delta,imm=ins(target+8);v.require((op,reg,imm)==(0x05,0,0) and target+16+delta*8==1032,'guard error jump differs')
    v.require(ins(488)==(0x18,3,0,-1530494976) and ins(496)==(0,0,0,232830),'guard price literal differs')
    fs=v.functions(e);calls=c.calls(v,w,fs);by_offset=dict(calls)
    for offset,tag in [(512,'O0439'),(552,'O0430'),(624 if checked else 984,'O0430')]:v.require(by_offset.get(offset)==('local',*v.shape(originals[tag])),'guard price/delta callee differs')
    original_calls=c.calls(v,originals['O0082'],{w['start']:w for w in originals.values()});prefix=[x[1] for x in calls[:7]]==[x[1] for x in original_calls[:7]]
    v.require(prefix==checked,'guard original seven-callee prefix differs')
    return dict(mask_offset=off,branch_offset=off+8,branch_opcode=opcode,branch_target=target,guard_hex=e.b[w['start']+off:w['start']+off+16].hex(),price_multiply=512,price_divide=552,delta_divide=624 if checked else 984,first_seven_callee_identities_equal_original=prefix,first_seven_offsets=[x[0] for x in calls[:7]],error_tag_block=952 if checked else None,error_construction_block=1032 if checked else None,scope='Exact syntactic mask, branch, immediate and normalized callee witnesses; no whole CFG or behavior proof.')

def verify(root=HERE,check_manifest=True):
    parent=root.parent.parent.parent;v=module('guard_parent',parent/'verify.py');c=module('guard_composition',root.parent.parent/'verify.py');a=module('guard_arithmetic',root.parent/'verify.py');reader=module('guard_reader',parent/'reader.py')
    if check_manifest:v.manifest_check(parent)
    v.require(v.identity((parent/'reader.py').read_bytes())['sha256']==v.read(parent/'scope.json')['reader_sha256'],'guard reader differs')
    base=c.sources(root.parent.parent,v);images={};results={};records={}
    with tempfile.TemporaryDirectory(prefix='mayhem-guard-') as tmp:
        def elf(name,b):p=Path(tmp)/name;p.write_bytes(b);return reader.Elf(p)
        original=elf('original.so',v.raw(parent/'reference/original.so.gz'));v.require(v.identity(original.b)['sha256']==v.ORIGINAL,'guard original differs')
        originals={r['id']:original.window(r['start'],r['end']) for r in v.read(parent/'reference/original-windows.json')}
        old_folder=root.parent.parent/'builds/late-inline';old_launch=v.read(old_folder/'launch.json.gz');baseline=c.measure(v,elf('baseline.so',v.raw(old_folder/'symbols.so.gz')),original,originals)
        for label in LABELS:
            folder=root/'builds'/label;launch=v.read(folder/'launch.json.gz');receipt=v.read(folder/'result.json.gz');canonical=label.removesuffix('-repeat');pf=old_folder if canonical.startswith('checked') else root.parent/'builds/overflow-late';prior=v.read(pf/'launch.json.gz')
            inputs=variant(root,v,c,a,base,label)
            v.require(launch['source_inputs']=={n:v.identity(b)['sha256'] for n,b in inputs.items()} and launch['parent_source_inputs']==prior['source_inputs'] and launch['changed_source_files']==['src/instructions/pump_interface.rs'],'guard build source binding differs')
            v.require(launch['transform']==dict(zip(('old','new'),[x.decode() for x in TRANSFORMS[canonical]])),'guard transform receipt differs')
            v.require(launch['parent_launch_sha256']==v.identity(v.raw(pf/'launch.json.gz'))['sha256'] and launch['compiler_parent_launch_sha256']==v.identity(v.raw(old_folder/'launch.json.gz'))['sha256'],'guard parent launch binding differs')
            v.require(all(launch[k]==old_launch[k] for k in ('checked_executables','reused_dependencies')),'guard compiler/dependencies differ')
            command=old_launch['command'][:];command[command.index('--out-dir')+1]=launch['command'][launch['command'].index('--out-dir')+1]
            if not label.endswith('repeat'):command+=['-C','llvm-args=-print-after=codegenprepare,finalize-isel','-C','llvm-args=-filter-print-funcs='+a.FUNCTION]
            v.require(command==launch['command'],'guard compiler command differs')
            v.require(receipt['status']=='SUCCEEDED' and receipt['returncode']==0 and receipt['target_executions']==0 and receipt['source_unchanged'] and receipt['dependencies_unchanged'] and receipt['strip']['returncode']==0,'guard failed/unexecuted compilation')
            images[label]={n:v.raw(folder/(n+'.gz')) for n in receipt['outputs']};v.require({n:v.identity(b) for n,b in images[label].items()}==receipt['outputs'],'guard output binding differs');records[label]=receipt['outputs']
            e=elf(label+'.so',images[label]['symbols.so']);strip=elf(label+'-strip.so',images[label]['candidate-v154-strip.so']);v.require(v.allocated(e)==v.allocated(strip),'guard strip changes allocations');v.require(e.b!=original.b and strip.b!=original.b,'guard unexpected whole original equality')
            if label.endswith('repeat'):continue
            row=c.measure(v,e,original,originals);inv=row['inventory'];bi=baseline['inventory'];v.require((inv['normalized'],inv['raw_local'],inv['injective'])==(432,77,431),'guard inventory differs')
            v.require(inv['raw_ids']==bi['raw_ids'] and {k for k,m in inv['matches'].items() if m}=={k for k,m in bi['matches'].items() if m} and row['positive_internal_calls']==baseline['positive_internal_calls'] and row['positive_internal_call_count']==4314,'guard exact match/call sets differ')
            v.require(all(not h['complete_shape_equal'] and h['callee_multiset_equal'] for h in row['handlers'].values()),'guard complete body/callee scope differs')
            for tag in ('O0081','O0083','O0084'):v.require(all(row['handlers'][tag][k]==baseline['handlers'][tag][k] for k in ('bytes','normalized_sha256','normalization_pattern','candidate_calls')),'guard changes another handler')
            h=row['handlers']['O0082'];checked=canonical.startswith('checked');v.require((h['bytes'],h['bump_read']['offset'],h['diagnostic_aligned_slots'],h['ordered_matches'])==((12912,6200,995,46) if checked else (12904,6192,980,45)),'guard diagnostics differ')
            w=c.body(v,e,originals,'sell','O0082')[0];row['byte_witness']=witness(v,c,e,w,originals,label);log=v.raw(folder/'stderr.log.gz').decode('utf-8');ir=a.ir_order(v,a.ir_fragment(v,log,'CodeGen Prepare (codegenprepare)'))
            v.require(ir['price_before_guard'] and ir['guard_has_profile_metadata']==checked,'guard IR profile/position differs')
            v.require((ir['price_divide']<ir['multiply_overflow'])==checked,'guard IR multiplication position differs')
            row['ir']=ir;row['machine']=a.machine_trace(v,log,'After Finalize ISel and expand pseudo-instructions (finalize-isel)',e);v.require(row['machine']['call_count']==83,'guard MIR call count differs');results[label]=row
        v.require(images['checked-price-first-late']==images['checked-price-first-late-repeat'],'guard complete repeat differs')
    fresh=root/'rebuild-validation';receipt=v.read(fresh/'result.json.gz');comparison=v.read(fresh/'comparison.json.gz');launch=v.read(fresh/'launch.json.gz');prior=v.read(root/'builds/checked-price-first-late/launch.json.gz')
    v.require(receipt['status']=='SUCCEEDED' and receipt['returncode']==0 and receipt['source_unchanged'] and receipt['root_invocations']==1 and receipt['target_executions']==0 and receipt['strip']['returncode']==0,'guard fresh build incomplete')
    v.require(comparison['outputs_equal'] and comparison['variant']=='checked-price-first-late' and comparison['actual']==comparison['expected']==receipt['outputs']==records['checked-price-first-late'],'guard fresh output/variant differs')
    v.require(launch['target_directory_initially_absent'] and launch['source_inputs']==prior['source_inputs'] and launch['checked_executables']==prior['checked_executables'],'guard fresh source/tool binding differs')
    for name,pin in receipt['logs'].items():v.require(v.identity(v.raw(fresh/(name+'.gz')))==pin,'guard fresh log differs')
    commands=[json.loads(b) for b in v.unpack((fresh/'wrapper-records.tar.gz').read_bytes()).values()]
    commands=[r for r in commands if '--crate-name' in r['after'] and any(a in r['after'] for a in ('--emit=dep-info,link','--emit=dep-info,metadata,link'))]
    targets=[r for r in commands if '--target' in r['after'] and r['after'][r['after'].index('--target')+1]=='sbpf-solana-solana'];v.require((len(commands),len(targets))==(163,85),'guard fresh compiler cohort differs')
    metadata=[line.split('\t') for line in (parent/'controller/metadata-map.tsv').read_text().splitlines()]
    for command in targets:
        before=[a[9:] for a in command['before'] if a.startswith('metadata=')];after=[a[9:] for a in command['after'] if a.startswith('metadata=')];name=command['after'][command['after'].index('--crate-name')+1]
        v.require(len(before)==len(after)==1 and [before[0],after[0],name] in metadata,'guard fresh metadata binding differs')
    return json.loads(json.dumps(dict(builds=results,outputs=records,successful_root_compilations=3,fresh_dependency_builds=1,fresh_compiler_commands=163,fresh_target_commands=85,fresh_complete_outputs_equal=True,complete_repeat_pairs=1,complete_windows_gained=0,target_executions=0,scope='Ordinary source controls; neither restores the whole handler or original error-block layout. Original-source identity and behavior remain unproved.')))

if __name__=='__main__':
    r=verify();v=module('guard_report',HERE.parent.parent.parent/'verify.py');v.require(r==v.read(HERE/'report.json.gz'),'guard saved report differs');print('Verified three guard controls: price-first checked multiplication restores the initial callee prefix and branch polarity; whole handler remains unmatched.')
