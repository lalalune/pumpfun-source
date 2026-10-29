"""Static replay of the existing reverse-local option and store-order controls."""
if not __debug__:raise SystemExit('Run without -O.')
from pathlib import Path
import gzip,hashlib,json,re,tempfile
P=Path(__file__).resolve().parent
SYMBOL='_ZN14pump_recovered5trade12v3_buy_costs17h280dba79c4dad174E'
PAIR=b'  %49 = getelementptr inbounds i8, ptr %_0, i64 8\r\n  store i64 %_84.0, ptr %49, align 8\r\n  %50 = getelementptr inbounds i8, ptr %_0, i64 16\r\n  store ptr %_84.1, ptr %50, align 8\r\n'
REVERSED=b'  %49 = getelementptr inbounds i8, ptr %_0, i64 8\r\n  %50 = getelementptr inbounds i8, ptr %_0, i64 16\r\n  store ptr %_84.1, ptr %50, align 8\r\n  store i64 %_84.0, ptr %49, align 8\r\n'
def need(ok,message):
    if not ok:raise ValueError(message)
def sha(b):return hashlib.sha256(b).hexdigest()
def data(key):return gzip.decompress((P/'evidence'/(key+'.gz')).read_bytes())
def record(key):return json.loads(data(key))
def text(key):return data(key).decode().replace('\r\n','\n')
def input_delta(before,after):
    need(before.count(PAIR)==1 and after==before.replace(PAIR,REVERSED),'only the two disjoint result stores change order')
def command_check(launch,base,flags,tool,input_bytes):
    expected=base['command'][:11]
    for i in [0,8,10]:expected[i]=launch['command'][i]
    need(launch['command']==expected+flags and launch['environment']==base['environment'],'literal supported-option recipe')
    need(launch['tool_sha256']==tool and launch['input_sha256']==sha(input_bytes),'compiler/input binding')
def allocation(t,active):
    rows=re.findall(r'^selectOrSplit GPR:%(100|101) \[(\d+)r,(\d+)r:0\)',t,re.M)
    expected=[('101','6368','6400'),('100','6352','6384')] if active else [('100','6352','6400'),('101','6368','6384')]
    need(rows==expected,'ordered field interval endpoints')
    assigned=re.findall(r'^assigning %(100|101) to \$(r\d+):',t,re.M)
    need(assigned==[(expected[0][0],'r1'),(expected[1][0],'r2')],'field colors')
    need('V3_FIELD_COUNTERFACTUAL' not in t and 'FIELD_PROBE' not in t,'no private field instrumentation')
    return dict(intervals=rows,assignments=assigned,derived_reverse_priorities={r:(1<<31)+int(end)//4 for r,start,end in rows})
def verify(repo,parent,api,original):
    inventory=parent.record('compiler/source-inventory.json');hypothesis=record('stock-priority/hypothesis.json')
    for path,digest in hypothesis['sources'].items():need(sha(data('compiler/'+path))==digest==inventory[path],'pinned option implementation')
    cpp=text('compiler/llvm/lib/CodeGen/RegAllocGreedy.cpp')
    need('Prio = Indexes->getZeroIndex().getApproxInstrDistance(LI.endIndex());' in cpp and 'ReverseLocalAssignment = GreedyReverseLocalAssignment.getNumOccurrences()' in cpp,'end-distance option implementation')
    need('virtual bool reverseLocalAssignment() const { return false; }' in text('compiler/llvm/include/llvm/CodeGen/TargetRegisterInfo.h') and 'reverseLocalAssignment' not in text('compiler/llvm/lib/Target/SBF/SBFRegisterInfo.h'),'stock target default')
    stock='aff85aa14d18e21b98f6e17f9e4b80c26c5ed0948b9641af46d73881a3c2ab6d';scheduler='89fcc76c5c3c94613ff93984a0afee87628a64fad499d0c54ece3dc88547032f'
    cases=[(m,r,False,False) for m in ['baseline','frequency'] for r in [False,True]]+[('frequency',True,True,False)]+[(m,r,False,True) for m in ['baseline','frequency'] for r in [False,True]]
    outputs={};rows={}
    with tempfile.TemporaryDirectory(prefix='v3-stock-priority-') as tmp:
        def elf(raw,name):
            p=Path(tmp)/name;p.write_bytes(raw);return api.Elf(p)
        base=elf(parent.data('extracted/target.o'),'base.o');_,base_refs=parent.symbol_object(base,SYMBOL)
        ob=original.body(0x80df8,2120);on=original.normalize(ob,0x80df8)[0]
        for mode,reverse,sched,stores in cases:
            name=('stores-'+mode+'-reverse'+str(int(reverse))) if stores else mode+'-reverse'+str(int(reverse))+'-scheduler'+str(int(sched))
            key='stock-priority/'+name;l=record(key+'/launch.json');r=record(key+'/result.json');inp=parent.data('costs/ir01/'+mode+'/input.ll');launch=parent.record('costs/ir01/'+mode+'/launch.json')
            if stores:
                changed=data('stock-priority/stores-'+mode+'.ll');input_delta(inp,changed);inp=changed
            flags=(['-v3-diagnostic-reverse-loads'] if sched else [])+['-greedy-reverse-local-assignment='+str(reverse).lower(),'-debug-only='+('isel-dump,pre-RA-sched,regalloc' if stores else 'regalloc'),'-print-before=greedy','-print-after=greedy,virtregrewriter','-filter-print-funcs='+SYMBOL]
            command_check(l,launch,flags,scheduler if sched else stock,inp)
            need(l['controller_sha256']==sha(data('stock-priority/'+('run_stores.py' if stores else 'run.py'))),'controller binding')
            need(r['returncode']==0 and r['input_unchanged'] and r['tool_unchanged'] and r['target_executions']==0,'compiler receipt')
            for n,x in r['logs'].items():need(sha(data(key+'/'+n))==x['sha256'] and len(data(key+'/'+n))==x['bytes'],'log binding')
            b=data(key+'/target.o');need(sha(b)==r['object_sha256'],'object binding');outputs[name]=b
            need('v3-diagnostic-field-priority' not in ' '.join(l['command']),'no private priority option')
            trace=text(key+'/stderr.log');need(trace.count('V3_SCHED_COUNTERFACTUAL')==int(sched),'exact remaining private scheduler intervention')
            if not sched and not stores:need(b==parent.data('costs/ir01/'+mode+'/target.o'),'stock flag alone whole object unchanged')
            if stores and reverse:need(b==outputs['stores-'+mode+'-reverse0'],'reverse option does not rescue store order')
            if not reverse:need(r['whole_parent_object_equal'] and sha(b)==l['parent_object_sha256'],'explicit-off complete object qualification')
            e=elf(b,name+'.o');raw,refs=parent.symbol_object(e,SYMBOL);normal=parent.normalize_object(raw,refs);constants=parent.bind_objects(base,e,base_refs,refs,same_offsets=False)
            need(constants==13,'complete constant bindings')
            measure=dict(object_sha256=sha(b),target_bytes=len(raw),normalized_slots=parent.distance(on,normal),raw_original_equal=raw==ob,normalized_original_equal=normal==on,constant_objects_bound=constants)
            if mode=='frequency':measure['allocation']=allocation(trace,sched)
            rows[name]=measure
        final=outputs['frequency-reverse1-scheduler1']
        need(final==data('fields/repaired-scheduler1-priority1/target.o'),'existing option replaces private field patch byte for byte')
        need(rows['frequency-reverse1-scheduler1']['normalized_original_equal'] and not rows['frequency-reverse1-scheduler1']['raw_original_equal'],'normalized-only boundary')
        for mode,expected in [('baseline',(2152,26)),('frequency',(2144,9))]:
            for rev in [0,1]:
                row=rows['stores-'+mode+'-reverse'+str(rev)];need((row['target_bytes'],row['normalized_slots'])==expected,'retained negative store-order control')
    return dict(result='PASS',llc_commands=9,root_rustc_commands=0,host_build_commands=0,target_executions=0,private_priority_patch_required=False,private_scheduler_patch_still_required=True,measurements=rows,scope='Existing allocator option reproduces the private field-priority result, with synthetic profile and one remaining private scheduler intervention. Store-order alternative fails. No recovered source, raw identity or original option provenance.')
