"""Replay retained arithmetic-lowering evidence; no compiler, VM or network use."""
if not __debug__:
    raise RuntimeError('Evidence checks require ordinary Python')
from pathlib import Path
import hashlib,importlib.util,json,re,struct,tempfile
HERE=Path(__file__).resolve().parent
FUNCTION='_ZN16mayhem_recovered12instructions14pump_interface19legacy_sell_handler17hf2e4c78980301589E'
LABELS=('baseline-stages','baseline-preisel','overflow-early','overflow-late','overflow-early-repeat','overflow-late-repeat')
TRANSFORMS=(
    (b'  let scaled=reference.checked_mul(tolerance_bps as u128);',b'  let (scaled,overflow)=reference.overflowing_mul(tolerance_bps as u128);'),
    (b'  let delta=scaled.ok_or(MayhemError::MathOverflow)?/10_000;',b'  let delta=if overflow{return Err(MayhemError::MathOverflow);}else{scaled}/10_000;'))

def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def variant(root,v,c,base,label):
    v.require(label in LABELS,'unknown arithmetic source')
    parent='late-inline' if 'late' in label else 'baseline'
    out=c.variant(root.parent,v,base,parent)
    if label.startswith('overflow'):
        name='src/instructions/pump_interface.rs';original=out[name];b=original
        for a,z in TRANSFORMS:
            v.require(b.count(a)==1,'arithmetic source anchor differs');b=b.replace(a,z)
        v.require(b.count(b'\n')==original.count(b'\n'),'arithmetic source lines shifted')
        def origin(s):i=s.index(b'error!(MayhemError::PumpCpiFailed)');return s[:i].count(b'\n'),i-s.rfind(b'\n',0,i)
        v.require(origin(b)==origin(original),'arithmetic CPI source origin shifted')
        v.require(b==(root/'sources'/('overflow-late.rs' if 'late' in label else 'overflow-early.rs')).read_bytes(),'arithmetic source transform differs')
        out[name]=b
    return out

def ir_fragment(v,log,pass_name):
    marker='*** IR Dump After '+pass_name+' ***'
    v.require(log.count(marker)==1,'unique arithmetic IR stage required');a=log.index(marker);a=log.index('define ',a);z=log.index('\n}',a)+2;s=log[a:z]
    v.require('@'+FUNCTION+'(' in s.splitlines()[0],'arithmetic IR function differs');return s

def ir_order(v,fragment):
    """Bind arithmetic and guard to actual SSA values, not line-number guesses."""
    lines=fragment.splitlines()
    def one(pattern):
        hits=[(i+1,re.search(pattern,l)) for i,l in enumerate(lines) if re.search(pattern,l)]
        v.require(len(hits)==1,'arithmetic SSA witness differs');return hits[0]
    mult,m=one(r'(%\d+) = tail call \{ i128, i1 \} @llvm\.umul\.with\.overflow\.i128\(');product=m[1]
    flag,f=one(r'(%\d+) = extractvalue \{ i128, i1 \} '+re.escape(product)+r', 1$')
    guard,g=one(r'br i1 '+re.escape(f[1])+r', label %[^,]+, label %[^,]+(.*)$')
    mul,p=one(r'(%\d+) = mul nuw nsw i128 %\d+, 1000000000000000$')
    div,_=one(r'(%\d+) = udiv i128 '+re.escape(p[1])+r', %\d+$')
    low,l=one(r'(%\d+) = extractvalue \{ i128, i1 \} '+re.escape(product)+r', 0$')
    delta,_=one(r'(%\d+) = udiv i128 '+re.escape(l[1])+r', 10000$')
    v.require(mult<flag<guard and mul<div<delta and low<delta,'arithmetic SSA order differs')
    return dict(fragment_sha256=hashlib.sha256(fragment.encode()).hexdigest(),multiply_overflow=mult,overflow_flag=flag,guard=guard,price_multiply=mul,price_divide=div,delta_divide=delta,guard_has_profile_metadata='!prof' in g[1],price_before_guard=div<guard)

def machine_trace(v,log,stage,e):
    marker='# *** IR Dump '+stage+' ***:'
    v.require(log.count(marker)==1,'unique arithmetic MIR stage required');a=log.index(marker);end='# End machine code for function '+FUNCTION+'.';z=log.index(end,a)+len(end);s=log[a:z]
    v.require(s.count('# Machine code for function '+FUNCTION+':')==1,'arithmetic MIR function differs')
    fs=v.functions(e);symbols={};imports={x['name'] for x in e.symbols if x['table']=='.dynsym'}
    for x in e.symbols:symbols.setdefault(x['name'],set()).add(x['value'])
    calls=[];names=[];slot_lines=0
    for line in s.splitlines():
        cleaned=re.sub(r'^\d+[Berd]\s+','',line);slot_lines+=cleaned!=line
        call=re.match(r'\s*JAL\s+[@&]("[^"]+"|[^,]+),',cleaned)
        if call:
            name=call[1].strip('"');values=symbols.get(name,set());v.require(len(values)<=1,'ambiguous MIR symbol');address=next(iter(values),None)
            if address in fs:identity=('local',*v.shape(fs[address]))
            else:v.require(name in imports,'MIR target lacks ELF binding');identity=('import',name)
            names.append(name);calls.append(identity)
        elif re.search(r'\bJAL\w*\b',cleaned):v.require(False,'unparsed arithmetic MIR call')
    v.require(calls,'empty arithmetic MIR calls')
    return dict(fragment_sha256=hashlib.sha256(s.encode()).hexdigest(),call_count=len(calls),slot_index_lines=slot_lines,callee_names=names,callee_identities=calls)

def byte_witness(v,c,e,w,originals,label):
    """Syntactic instruction/target witnesses; no symbolic execution claim."""
    expected={'original':(592,9,0x55,1960),'baseline':(512,3,0x55,1864),'overflow-early':(552,8,0x15,928),'overflow-late':(560,6,0x15,936)}
    offset,reg,opcode,target=expected[label]
    def ins(off):return struct.unpack_from('<BBhi',e.b,w['start']+off)
    v.require(ins(offset)==(0x57,reg,0,1),'arithmetic low-bit mask differs')
    op,r,delta,imm=ins(offset+8);v.require((op,r,imm)==(opcode,reg,0) and offset+16+delta*8==target,'arithmetic guard branch differs')
    constants=[]
    for off in range(0,1200,8):
        op,r,d,lo=ins(off)
        if op==0x18 and r==3:
            op2,r2,d2,hi=ins(off+8)
            if (lo&0xffffffff)+(hi&0xffffffff)*2**32==10**15:
                v.require((op2,r2,d2)==(0,0,0),'price constant continuation differs');constants.append(off)
    v.require(len(constants)==1,'unique price constant required');mul=constants[0]+24;div=mul+40
    targets={x['start']:x for x in originals.values()} if label=='original' else v.functions(e)
    calls=dict(c.calls(v,w,targets))
    for off,tag in [(mul,'O0439'),(div,'O0430')]:v.require(calls.get(off)==('local',*v.shape(originals[tag])),'price call target differs')
    deltas=[off+16 for off in range(0,1200,8) if ins(off)==(0xb7,3,0,10000) and calls.get(off+16)==('local',*v.shape(originals['O0430']))]
    v.require(len(deltas)==1,'delta divide witness differs')
    return dict(mask_offset=offset,mask_register=reg,branch_opcode=opcode,branch_target=target,guard_hex=e.b[w['start']+offset:w['start']+offset+16].hex(),price_constant_offset=constants[0],price_multiply=mul,price_divide=div,delta_divide=deltas[0],price_before_guard=div<offset,guard_taken_when='nonzero' if opcode==0x55 else 'zero',scope='Syntactic low-bit mask/branch, literal and normalized direct-callee witnesses; not a CFG or runtime proof.')

def verify(root=HERE,check_manifest=True):
    parent=root.parent.parent;v=module('arithmetic_parent',parent/'verify.py');c=module('arithmetic_composition',root.parent/'verify.py');reader=module('arithmetic_reader',parent/'reader.py')
    if check_manifest:v.manifest_check(parent)
    v.require(v.identity((parent/'reader.py').read_bytes())['sha256']==v.read(parent/'scope.json')['reader_sha256'],'arithmetic reader differs')
    base=c.sources(root.parent,v);up=root/'upstream';acq=v.read(up/'acquisition.json');pins=v.read(up/'source-inputs.json');manifest=v.read(up/'manifest.json')
    v.require(acq['revision']=='a600dd2617cf9d062b0a602204fb8419e9e8c108','overflow upstream revision differs')
    for name,pin in acq['files'].items():
        b=(up/v.safe(name)).read_bytes();v.require(v.identity(b)=={k:pin[k] for k in ('bytes','sha256')} and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==pin['git_blob'],'overflow upstream Git blob differs')
        if name!='manifest.json':v.require(v.identity(b)['sha256']==manifest[name],'overflow upstream manifest differs')
    early=variant(root,v,c,base,'overflow-early');native_pins={n:v.identity(b)['sha256'] for n,b in early.items()}
    v.require(len(native_pins)==67 and [n for n in native_pins if native_pins[n]!=pins['overflowing-product'][n]]==['src/instructions/buy_v2.rs'],'overflow upstream source bridge differs')
    for name in ('src/instructions/pump_interface.rs','src/state.rs'):v.require(early[name]==v.raw(up/'builds/overflowing-product/overrides'/(name+'.gz')),'overflow retained source differs')
    images={};results={};diagnostics={}
    with tempfile.TemporaryDirectory(prefix='mayhem-arithmetic-') as tmp:
        def elf(name,b):p=Path(tmp)/name;p.write_bytes(b);return reader.Elf(p)
        original=elf('original.so',v.raw(parent/'reference/original.so.gz'));v.require(v.identity(original.b)['sha256']==v.ORIGINAL,'arithmetic original differs')
        originals={r['id']:original.window(r['start'],r['end']) for r in v.read(parent/'reference/original-windows.json')}
        witnesses={'original':byte_witness(v,c,original,originals['O0082'],originals,'original')}
        prior_folder=root.parent/'builds/baseline';baseline=elf('baseline.so',v.raw(prior_folder/'symbols.so.gz'));baseline_row=c.measure(v,baseline,original,originals)
        witnesses['baseline']=byte_witness(v,c,baseline,c.body(v,baseline,originals,'sell','O0082')[0],originals,'baseline')
        upstream=elf('upstream.so',v.raw(up/'builds/overflowing-product/symbols.so.gz'));uw=c.body(v,upstream,originals,'sell','O0082')[0]
        for label in LABELS:
            folder=root/'builds'/label;launch=v.read(folder/'launch.json.gz');receipt=v.read(folder/'result.json.gz');parent_label='late-inline' if 'late' in label else 'baseline';pf=root.parent/'builds'/parent_label;pl=v.read(pf/'launch.json.gz')
            inputs=variant(root,v,c,base,label);v.require(launch['source_inputs']=={n:v.identity(b)['sha256'] for n,b in inputs.items()},'arithmetic build source binding differs')
            if label.startswith('overflow'):v.require(launch['parent_source_inputs']==pl['source_inputs'] and launch['changed_source_files']==['src/instructions/pump_interface.rs'],'arithmetic parent source binding differs')
            v.require(launch['parent_launch_sha256']==v.identity(v.raw(pf/'launch.json.gz'))['sha256'] and all(launch[k]==pl[k] for k in ('checked_executables','reused_dependencies')),'arithmetic compiler/dependency context differs')
            v.require(len(launch['reused_dependencies'])==104,'arithmetic dependency cohort differs')
            command=pl['command'][:];command[command.index('--out-dir')+1]=launch['command'][launch['command'].index('--out-dir')+1]
            flags=[]
            if label=='baseline-stages':flags=['-debug-pass=Arguments','-print-after=finalize-isel,machine-sink,machine-scheduler','-print-before=machine-sink,machine-scheduler']
            elif label=='baseline-preisel':flags=['-print-before=sbf-isel','-print-after=expand-large-div-rem,sbf-check-and-opt-ir,codegenprepare']
            elif not label.endswith('repeat'):flags=['-print-after=codegenprepare,finalize-isel']
            if flags:flags.append('-filter-print-funcs='+FUNCTION)
            for flag in flags:command+=['-C','llvm-args='+flag]
            v.require(command==launch['command'],'arithmetic compiler command differs')
            v.require(receipt['status']=='SUCCEEDED' and receipt['returncode']==0 and receipt['target_executions']==0 and receipt['source_unchanged'] and receipt['dependencies_unchanged'] and receipt['strip']['returncode']==0,'arithmetic failed/unexecuted compilation')
            outputs={n:v.raw(folder/(n+'.gz')) for n in receipt['outputs']};v.require({n:v.identity(b) for n,b in outputs.items()}==receipt['outputs'],'arithmetic output binding differs');images[label]=outputs
            e=elf(label+'.so',outputs['symbols.so']);strip=elf(label+'-strip.so',outputs['candidate-v154-strip.so']);v.require(v.allocated(e)==v.allocated(strip),'arithmetic strip changes allocated sections')
            v.require(e.b!=original.b and strip.b!=original.b,'unexpected whole original equality')
            if label.startswith('baseline'):
                v.require(all(b==v.raw(pf/(n+'.gz')) for n,b in outputs.items()) and receipt['complete_outputs_equal_parent'],'arithmetic diagnostic changes complete outputs')
            elif not label.endswith('repeat'):
                row=c.measure(v,e,original,originals);results[label]=row;inv=row['inventory'];bi=baseline_row['inventory']
                v.require((inv['normalized'],inv['raw_local'],inv['injective'])==(432,77,431),'arithmetic native inventory differs')
                v.require(inv['raw_ids']==bi['raw_ids'] and {k for k,a in inv['matches'].items() if a}=={k for k,a in bi['matches'].items() if a},'arithmetic exact match set differs')
                v.require(row['positive_internal_calls']==baseline_row['positive_internal_calls'] and row['positive_internal_call_count']==4314,'arithmetic positive call set differs')
                for tag in ('O0081','O0083','O0084'):
                    v.require(all(row['handlers'][tag][k]==baseline_row['handlers'][tag][k] for k in ('bytes','normalized_sha256','normalization_pattern','candidate_calls')),'arithmetic changes another handler')
                v.require(all(not h['complete_shape_equal'] and h['callee_multiset_equal'] for h in row['handlers'].values()),'arithmetic whole body/callee scope differs')
                h=row['handlers']['O0082'];expect=(12896,2400,621,46) if label=='overflow-early' else (12912,6200,985,46)
                v.require((h['bytes'],h['bump_read']['offset'],h['diagnostic_aligned_slots'],h['ordered_matches'])==expect,'arithmetic diagnostic measurement differs')
                w=c.body(v,e,originals,'sell','O0082')[0];witnesses[label]=byte_witness(v,c,e,w,originals,label)
                if label=='overflow-early':v.require(v.shape(w)==v.shape(uw) and c.calls(v,w,v.functions(e))==c.calls(v,uw,v.functions(upstream)),'native overflow differs from upstream whole normalized handler/calls')
            log=v.raw(folder/'stderr.log.gz').decode('utf-8')
            if label=='baseline-stages':
                stages=['After Finalize ISel and expand pseudo-instructions (finalize-isel)','Before Machine code sinking (machine-sink)','After Machine code sinking (machine-sink)','Before Machine Instruction Scheduler (machine-scheduler)','After Machine Instruction Scheduler (machine-scheduler)']
                traces=[machine_trace(v,log,s,e) for s in stages]
                v.require(all(t['call_count']==83 and t['callee_identities']==traces[0]['callee_identities'] for t in traces),'arithmetic stage call sequences differ')
                v.require(all(t['slot_index_lines']>0 for t in traces[-2:]),'scheduler SlotIndex evidence missing')
                diagnostics[label]=dict(stages=stages,traces=traces,pass_arguments=[l for l in log.splitlines() if l.startswith('Pass Arguments:')])
            elif not label.endswith('repeat'):
                ir=ir_order(v,ir_fragment(v,log,'CodeGen Prepare (codegenprepare)'));overflow=label.startswith('overflow')
                v.require(ir['price_before_guard']==overflow and ir['guard_has_profile_metadata']!=overflow,'arithmetic IR price/guard ordering differs')
                diagnostics[label]=dict(ir=ir)
                if overflow:
                    trace=machine_trace(v,log,'After Finalize ISel and expand pseudo-instructions (finalize-isel)',e);diagnostics[label]['trace']=trace
                    v.require(trace['callee_identities'][2:6]==[('local',*v.shape(originals[t])) for t in ('O0439','O0439','O0439','O0430')],'overflow initial lowering sequence differs')
        for a,b in [('overflow-early','overflow-early-repeat'),('overflow-late','overflow-late-repeat')]:v.require(images[a]==images[b],'arithmetic complete repeat differs')
        v.require(diagnostics['baseline-stages']['traces'][0]['callee_identities'][2:7]==[('local',*v.shape(originals[t])) for t in ('O0439','O0439','O0430','O0439','O0430')],'baseline initial lowering sequence differs')
    fresh=root/'rebuild-validation';receipt=v.read(fresh/'result.json.gz');comparison=v.read(fresh/'comparison.json.gz');launch=v.read(fresh/'launch.json.gz');prior_launch=v.read(root/'builds/overflow-late/launch.json.gz')
    v.require(receipt['status']=='SUCCEEDED' and receipt['returncode']==0 and receipt['source_unchanged'] and receipt['root_invocations']==1 and receipt['target_executions']==0 and receipt['strip']['returncode']==0,'arithmetic fresh build incomplete')
    expected={n:v.identity(b) for n,b in images['overflow-late'].items()}
    v.require(comparison['outputs_equal'] and comparison['variant']=='overflow-late' and comparison['actual']==comparison['expected']==receipt['outputs']==expected,'arithmetic fresh output comparison differs')
    v.require(launch['target_directory_initially_absent'] and launch['source_inputs']==prior_launch['source_inputs'] and launch['checked_executables']==prior_launch['checked_executables'],'arithmetic fresh source/tool binding differs')
    for name,pin in receipt['logs'].items():v.require(v.identity(v.raw(fresh/(name+'.gz')))==pin,'arithmetic fresh log differs')
    records=[json.loads(b) for b in v.unpack((fresh/'wrapper-records.tar.gz').read_bytes()).values()]
    commands=[r for r in records if '--crate-name' in r['after'] and any(a in r['after'] for a in ('--emit=dep-info,link','--emit=dep-info,metadata,link'))]
    targets=[r for r in commands if '--target' in r['after'] and r['after'][r['after'].index('--target')+1]=='sbpf-solana-solana']
    v.require((len(commands),len(targets))==(163,85),'arithmetic fresh compiler cohort differs')
    metadata=[line.split('\t') for line in (parent/'controller/metadata-map.tsv').read_text().splitlines()]
    for command in targets:
        before=[a[9:] for a in command['before'] if a.startswith('metadata=')];after=[a[9:] for a in command['after'] if a.startswith('metadata=')];name=command['after'][command['after'].index('--crate-name')+1]
        v.require(len(before)==len(after)==1 and [before[0],after[0],name] in metadata,'arithmetic fresh metadata binding differs')
    guard=module('arithmetic_guard_reader',root/'guard/verify.py').verify(root/'guard',False);v.require(guard==v.read(root/'guard/report.json.gz'),'guard saved report differs')
    return json.loads(json.dumps(dict(builds=results,diagnostics=diagnostics,byte_witnesses=witnesses,successful_root_compilations=6,fresh_dependency_builds=1,fresh_compiler_commands=163,fresh_target_commands=85,fresh_complete_outputs_equal=True,complete_repeat_pairs=2,upstream_normalized_sell_and_calls_reproduced=True,guard_followup=dict(root_compilations=guard['successful_root_compilations'],fresh_dependency_builds=guard['fresh_dependency_builds'],complete_windows_gained=0),complete_windows_gained=0,target_executions=0,whole_original_equal=False,scope='Partial arithmetic/source-layout evidence, not recovered body, behavioral equivalence, historical source, CFG identity or recursive/data closure.')))

if __name__=='__main__':
    r=verify();v=module('arithmetic_report',HERE.parent.parent/'verify.py');v.require(r==v.read(HERE/'report.json.gz'),'arithmetic saved report differs');print('Verified six arithmetic root builds and a fresh full rebuild, exact output repeats and bounded IR/MIR/ELF witnesses; no complete handler gain.')
