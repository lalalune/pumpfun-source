"""Read-only replay of V3 scheduler/field-coloring diagnostics, not a build."""
if not __debug__:raise SystemExit('Run without -O: evidence readers require assertions.')
from pathlib import Path
import argparse,difflib,gzip,hashlib,importlib.util,json,re,tempfile,types
P=Path(__file__).resolve().parent
SYMBOL='_ZN14pump_recovered5trade12v3_buy_costs17h280dba79c4dad174E'
TOOLS={'stock':'aff85aa14d18e21b98f6e17f9e4b80c26c5ed0948b9641af46d73881a3c2ab6d','scheduler1':'b1a2eb87ca46a63027bdf1bc1f742581a3b72b79b1ef7f7c20f70b1d24529874','scheduler2':'89fcc76c5c3c94613ff93984a0afee87628a64fad499d0c54ece3dc88547032f','fields1':'f33da26f606881118d473856b29e8ab6a12ae955ced2c49c31e167425c972629','fields2':'d405c5a1e36b29b9579c63bb3ba754585eae2643e2c5235a9c019ae7e94efc75'}
def need(ok,msg):
    if not ok:raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def data(key):return gzip.decompress((P/'evidence'/(key+'.gz')).read_bytes())
def record(key):return json.loads(data(key))
def text(key):return data(key).decode().replace('\r\n','\n')
def module(key):
    m=types.ModuleType(key);m.__file__=str(P/key);exec(compile(data(key),m.__file__,'exec'),m.__dict__);return m
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def fields(t,scheduler,priority):
    rows=re.findall(r'^FIELD_PROBE enqueue reg=%(100|101) priority=(\d+) size=(\d+) begin=(\d+)r end=(\d+)r last=(\d+)B local=(\S+) preference=(\d+) stage=(\d+) reverse=(\d+)$',t,re.M)
    need(len(rows)==2 and t.count('FIELD_PROBE enqueue ')==2 and [r[0] for r in rows]==['100','101'],'unique ordered field priority records')
    expected_sizes=[32,32] if scheduler else [48,16]
    for i,row in enumerate(rows):
        reg,prio,size,begin,end,last,local,pref,stage,rev=row
        need(int(begin)==6352+16*i and int(last)==7040 and int(size)==expected_sizes[i] and int(end)==int(begin)+int(size),'field interval/size binding')
        need(int(local,0)!=0 and (pref,stage,rev)==('0','1','0'),'local unhinted forward assignment')
        expected=(1<<31)+(int(last)-int(begin))//4
        need(int(prio)==expected==[2147483820,2147483816][i],'independent local priority calculation')
    events=re.findall(r'^V3_FIELD_COUNTERFACTUAL reg=%(\d+) previous=(\d+) replacement=(\d+)$',t,re.M)
    active=scheduler and priority
    need(t.count('V3_FIELD_COUNTERFACTUAL')==len(events) and events==([('100','2147483820','2147483816'),('101','2147483816','2147483820')] if active else []),'exact field intervention count/values')
    assignments=re.findall(r'^assigning %(100|101) to \$(r\d+):',t,re.M)
    expected=[('101','r1'),('100','r2')] if active else [('100','r1'),('101','r2')]
    need(assignments==expected,'field allocation order and colors')
    candidates=re.findall(r'^FIELD_PROBE candidate reg=%(\d+) physical=\$(r\d+) interference=(\d+) hint=(\d+)$',t,re.M)
    first,second=('101','100') if active else ('100','101')
    need(t.count('FIELD_PROBE candidate ')==len(candidates) and candidates==[(first,'r1','0','0'),(second,'r1','1','0'),(second,'r2','0','0')],'observed first-free register interference')
    return dict(priority100=2147483820,priority101=2147483816,assignments=assignments,interventions=len(events))
def strip_field_logs(t):return re.sub(r'^FIELD_PROBE[^\n]*\n','',t,flags=re.M)
def recipe(launch,base,flags,tool):
    expected=base['command'][:11];expected[0]=launch['command'][0];expected[10]=launch['command'][10];expected+=flags
    need(launch['command']==expected and launch['environment']==base['environment'],'literal command/environment')
    need(launch['tool_sha256']==tool and launch['input_sha256']==base['input_sha256'],'pinned compiler/input')
def run(key,controller,base,flags,tool,failed=False):
    l=record(key+'/launch.json');r=record(key+'/result.json');recipe(l,base,flags,tool)
    need(l['controller_sha256']==sha(data(controller)),'controller binding')
    need(r['input_unchanged'] and r['tool_unchanged'] and r['target_executions']==0,'input/tool/execution receipt')
    for n,x in r['logs'].items():
        b=data(key+'/'+n);need(sha(b)==x['sha256'] and len(b)==x['bytes'],'log receipt binding')
    if failed:
        need(r['returncode']==2147483651 and r['object_sha256'] is None,'retained assertion failure')
        need('index out of bounds!' in text(key+'/stderr.log') and 'V3_FIELD_COUNTERFACTUAL' not in text(key+'/stderr.log'),'failure before priority replacement')
        return None
    need(r['returncode']==0,'successful compiler receipt');b=data(key+'/target.o');need(sha(b)==r['object_sha256'],'emitted object binding');return b
def verify(repo):
    actual={p.relative_to(P).as_posix():sha(p.read_bytes()) for p in P.rglob('*') if p.is_file() and p.name!='MANIFEST.json'}
    need(actual==read(P/'MANIFEST.json'),'packet seal')
    for key,row in read(P/'EVIDENCE.json').items():
        b=data(key);need(row['file']=='evidence/'+key+'.gz' and len(b)==row['bytes'] and sha(b)==row['sha256'],'evidence inventory')
    provenance=read(P/'PROVENANCE.json');parent=repo/'research'/provenance['parent_packet']
    need(sha((parent/'MANIFEST.json').read_bytes())==provenance['parent_manifest_sha256'],'parent seal')
    v=load('field_parent',parent/'verify.py');parent_report=v.verify(repo)
    source=load('field_source',repo/'research/pump-v3-branch-layout-20261029/verify.py');api=source.elf_reader()
    original=api.Elf(repo/'evidence/original/pump/deployed.so');need(sha(original.data)==provenance['original_sha256'],'original capture')
    inventory=v.record('compiler/source-inventory.json')
    for key in read(P/'EVIDENCE.json'):
        if key.startswith('compiler/'):need(sha(data(key))==inventory[key.removeprefix('compiler/')],'pinned LLVM source')
    cpp=text('compiler/llvm/lib/CodeGen/RegAllocGreedy.cpp');slots=text('compiler/llvm/include/llvm/CodeGen/SlotIndexes.h')
    need('Prio = LI.beginIndex().getApproxInstrDistance(Indexes->getLastIndex());' in cpp and 'Prio |= (1u << 31);' in cpp,'local-priority formula')
    slot_enum=re.search(r'enum Slot \{(.*?)\};',slots,re.S)[1]
    slot_enum=re.sub(r'//[^\n]*','',slot_enum)
    need([x.strip() for x in slot_enum.split(',')]==['Slot_Block','Slot_EarlyClobber','Slot_Register','Slot_Dead','Slot_Count'] and '/ Slot_Count;' in slots,'SlotIndex distance unit')
    outputs={};bases={m:v.record('costs/ir01/'+m+'/launch.json') for m in ['baseline','frequency']}
    schedule_flags=['-debug-only=isel-dump,pre-RA-sched','-filter-print-funcs='+SYMBOL]
    field_flags=['-debug-only=regalloc','-print-before=greedy','-print-after=greedy,virtregrewriter','-filter-print-funcs='+SYMBOL]
    for mode in ['baseline','frequency']:
        parent_object=v.data('costs/ir01/'+mode+'/target.o')
        for prefix,controller,tool in [('stock-','capture.py','stock'),('probe-','run_probe.py','scheduler1'),('counterfactual-','run_counterfactual.py','scheduler2'),('postra-','run_postra.py','stock')]:
            names=[prefix+mode] if prefix!='counterfactual-' else [prefix+mode+'-off',prefix+mode+'-on']
            for name in names:
                flags=schedule_flags.copy()
                if name.endswith('-on'):flags+=['-v3-diagnostic-reverse-loads']
                if prefix=='postra-':flags=['-post-RA-scheduler=true','-debug-only=post-RA-sched','-print-before=post-RA-sched','-print-after=post-RA-sched','-filter-print-funcs='+SYMBOL]
                key='scheduler/'+name;outputs[key]=run(key,'scheduler/controllers/'+controller,bases[mode],flags,TOOLS[tool])
                if prefix in ['stock-','probe-'] or name.endswith('-off'):need(outputs[key]==parent_object,'passive/default-off whole object')
    analyzer=module('scheduler/controllers/analyze.py');trace_results={}
    for mode in ['baseline','frequency']:
        stock=text('scheduler/stock-'+mode+'/stderr.log');probe=text('scheduler/probe-'+mode+'/stderr.log')
        need(analyzer.pointers(stock)==analyzer.pointers(re.sub(r'^SCHED_PROBE[^\n]*\n','',probe,flags=re.M)),'passive trace equality, only logs/block addresses removed')
        need(analyzer.pointers(probe)==analyzer.pointers(text('scheduler/counterfactual-'+mode+'-off/stderr.log')),'default-off complete scheduler trace')
        block,order=analyzer.schedule(probe)
        changed,other=analyzer.schedule(text('scheduler/counterfactual-'+mode+'-on/stderr.log'))
        need('BURRSort:LDist < RDist left=5 right=36 left_queue=10 right_queue=11 result=1' in block,'actual successor-distance comparison')
        need('BURRSort:(left->NodeQueueId > right->NodeQueueId) left=2 right=37 left_queue=5 right_queue=4 result=1' in block,'store queue tie')
        need([x['unit'] for x in order][4:10]==[37,2,3,4,36,5] and [x['unit'] for x in other][4:10]==[37,2,3,4,5,36],'only load pair scheduling control')
        need([(x['cycle'],x['unit']) for x in order if x['unit'] not in [5,36]]==[(x['cycle'],x['unit']) for x in other if x['unit'] not in [5,36]],'all other scheduled positions')
        enabled=text('scheduler/counterfactual-'+mode+'-on/stderr.log')
        need(enabled.count('V3_SCHED_COUNTERFACTUAL')==1 and 'V3_SCHED_COUNTERFACTUAL left=5 right=36 LDist=4 RDist=5 left_offset=0 right_offset=8' in changed,'one actual scheduler intervention')
        trace_results[mode]=dict(nodes=40,load_distances=[4,5],store_queue_ids=[4,5],scheduler_interventions=1)
    for mode in ['off','on']:
        sched=mode=='on';flags=(['-v3-diagnostic-reverse-loads'] if sched else [])+field_flags
        key='fields/trace-'+mode;outputs[key]=run(key,'fields/controllers/capture.py',bases['frequency'],flags,TOOLS['scheduler2'])
        need(outputs[key]==outputs['scheduler/counterfactual-frequency-'+mode],'Greedy trace whole output')
        key='scheduler/stages-'+mode;flags=schedule_flags+(['-v3-diagnostic-reverse-loads'] if sched else [])+['-print-after-all']
        outputs[key]=run(key,'scheduler/controllers/capture_stages.py',bases['frequency'],flags,TOOLS['scheduler2'])
        need(outputs[key]==outputs['scheduler/counterfactual-frequency-'+mode],'all-stages output')
        t=text(key+'/stderr.log');stage=analyzer.machine_stage(t,'virtregrewriter');colored=re.findall(r'\$(r[12]) = LDD_V1 %stack\.17, (0|8) ',stage['tail'])
        need(colored==([('r1','8'),('r2','0')] if sched else [('r1','0'),('r2','8')]),'scheduler-only field colors')
        folded=analyzer.machine_stage(t,'branch-folder');need(('STD_V1' in folded['tail'])==sched,'tail sharing consequence')
    field_results={}
    for repaired in [False,True]:
      for sched,priority in [(False,False),(True,False),(False,True),(True,True)]:
        name=('repaired-' if repaired else '')+f'scheduler{int(sched)}-priority{int(priority)}';key='fields/'+name
        flags=(['-v3-diagnostic-reverse-loads'] if sched else [])+(['-v3-diagnostic-field-priority'] if priority else [])+field_flags
        failed=not repaired and sched and priority
        out=run(key,'fields/controllers/'+('run_probe02.py' if repaired else 'run_probe.py'),bases['frequency'],flags,TOOLS['fields2' if repaired else 'fields1'],failed)
        if failed:continue
        outputs[key]=out;t=text(key+'/stderr.log');field_results[name]=fields(t,sched,priority)
        rewritten=analyzer.machine_stage(t,'virtregrewriter')
        physical=re.findall(r'\$(r[12]) = LDD_V1 %stack\.17, (0|8) ',rewritten['tail'])
        expected=([('r2','8'),('r1','0')] if priority else [('r1','8'),('r2','0')]) if sched else [('r1','0'),('r2','8')]
        need(physical==expected,'field-to-physical-register output')
        if not(sched and priority):
            parent_key='fields/trace-'+('on' if sched else 'off')
            need(out==outputs[parent_key],'default-off/inactive-guard complete object')
            need(strip_field_logs(t)==text(parent_key+'/stderr.log'),'logging-only complete Greedy trace')
    # Bind source deltas and host-build receipts; replay does not attest a fresh
    # host build or require private executables to exist on the reviewer machine.
    for group in ['scheduler','fields']:
      for index in [1,2]:
        prefix=group+'/derivative0'+str(index);plan=record(prefix+'/build-launch.json');built=record(prefix+'/build-result.json')
        tool=TOOLS[group+str(index)];need(built['outputs']['llc.exe']==tool and built['stock_build_unchanged'] and built['stock_source_unchanged'],'isolated build receipt')
        source_name='ScheduleDAGRRList.cpp' if group=='scheduler' else 'RegAllocGreedy.cpp'
        rel='llvm/lib/CodeGen/'+('SelectionDAG/' if group=='scheduler' else '')+source_name
        need(plan['stock_source_sha256']==sha(data('compiler/'+rel)) and plan['derivative_source_sha256']==sha(data(prefix+'/'+source_name)),'compiler source binding')
        patch_name='diagnostic.patch' if group=='scheduler' else 'counterfactual.patch'
        delta=''.join(difflib.unified_diff(text('compiler/'+rel).splitlines(True),text(prefix+'/'+source_name).splitlines(True),fromfile=rel,tofile=rel))
        need(delta==text(prefix+'/'+patch_name) and plan['patch_sha256']==sha(data(prefix+'/'+patch_name)),'compiler patch text')
        need([x['stage'] for x in built['stages']]==['compile','archive','link'],'three host stages')
        controller=('build_probe.py' if index==1 else ('build_counterfactual.py' if group=='scheduler' else 'build_probe02.py'))
        need(plan['controller_sha256']==sha(data(group+'/controllers/'+controller)),'build controller')
        for x in built['stages']:
            need(x['returncode']==0,'host build status')
            for n,h in x['logs'].items():need(h==sha(data(prefix+'/'+x['stage']+'.'+n+('.log' if group=='scheduler' else ''))),'host build log')
        if group=='fields':
            patch_key='fields/controllers/'+('field_patch.py' if index==1 else 'field_patch02.py')
            p=module(patch_key)
            need(plan['field_patch_sha256']==sha(data(patch_key)),'field patch controller')
            need(p.patch(text('compiler/'+rel))==text(prefix+'/'+source_name),'exact field patch')
            need(plan['scheduler_parent']['library_sha256']==record('scheduler/derivative02/build-result.json')['outputs']['LLVMSelectionDAG.lib'],'inherited scheduler library')
            need(plan['scheduler_parent']['build_result_sha256']==sha(data('scheduler/derivative02/build-result.json')),'inherited scheduler build receipt')
    p=module('scheduler/controllers/counterfactual_patch.py')
    need(p.patch(text('scheduler/derivative01/ScheduleDAGRRList.cpp'))==text('scheduler/derivative02/ScheduleDAGRRList.cpp'),'exact scheduler switch delta')
    measurements={}
    with tempfile.TemporaryDirectory(prefix='v3-field-replay-') as temp:
        temp=Path(temp)
        def elf(b,name):
            path=temp/name;path.write_bytes(b);return api.Elf(path)
        baseline=elf(v.data('extracted/target.o'),'baseline.o');base_raw,base_refs=v.symbol_object(baseline,SYMBOL)
        ob=original.body(0x80df8,2120);on=original.normalize(ob,0x80df8)[0]
        for i,(key,b) in enumerate(outputs.items()):
            e=elf(b,str(i)+'.o');raw,refs=v.symbol_object(e,SYMBOL);normal=v.normalize_object(raw,refs)
            # Post-RA whole-function controls may reorder reference sites.
            constants=v.bind_objects(baseline,e,base_refs,refs,same_offsets=False) if '/postra-' not in key else None
            measurements[key]=dict(object_sha256=sha(b),target_bytes=len(raw),target_raw_sha256=sha(raw),target_normalized_sha256=sha(normal),aligned_slots=v.distance(on,normal),raw_original_equal=raw==ob,normalized_original_equal=normal==on,constant_objects_bound=constants)
        final=measurements['fields/repaired-scheduler1-priority1']
        need(final['object_sha256']=='2dc620ca0dae357214ce7af9c3b7af8fade5a622fd3716357625aba40821b527','combined emitted object')
        need(final['target_bytes']==2120 and final['aligned_slots']==0 and final['normalized_original_equal'] and not final['raw_original_equal'] and final['constant_objects_bound']==13,'normalized-only full-function boundary')
        for key,expected in [('fields/repaired-scheduler0-priority0',(2120,2)),('fields/repaired-scheduler1-priority0',(2144,9)),('fields/repaired-scheduler0-priority1',(2120,2)),('scheduler/postra-baseline',(2136,71)),('scheduler/postra-frequency',(2120,52))]:
            row=measurements[key];need((row['target_bytes'],row['aligned_slots'])==expected,'retained negative-control measurement')
    extension=load('existing_priority_option',P/'verify_stock_priority.py').verify(repo,v,api,original)
    return dict(result='PASS',parent_source_bytes=2136,parent_source_aligned_slots=23,trace=trace_results,fields=field_results,measurements=measurements,stock_priority=extension,combined_diagnostic_bytes=2120,combined_diagnostic_normalized_slots=0,raw_original_equal=False,ordered_call_sites=17,ordered_data_sites=16,constant_objects_bound=13,root_rustc_commands=0,llc_commands=31,failed_llc_commands=1,host_build_commands=12,target_executions=0,scope='Synthetic-profile diagnostic: existing allocator option replaces private priority patch; private scheduler intervention remains. No recovered Rust, original compiler recipe, linked raw identity, census gain, behavioral equivalence or security conclusion.')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--repo-root',type=Path,default=P.parents[1]);args=parser.parse_args();print(json.dumps(verify(args.repo_root.resolve()),indent=2))
