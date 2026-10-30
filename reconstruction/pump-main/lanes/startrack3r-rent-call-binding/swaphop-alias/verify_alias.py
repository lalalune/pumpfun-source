#!/usr/bin/env python3
"""Replay static swap-hop evidence; never compile or execute a target."""
import argparse,gzip,json,re,struct,sys
from collections import Counter,defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from verify_rent_edges import calls,formatter_span,require,sha

def read(p):return json.loads(p.read_bytes())
def gz(p):return json.loads(gzip.decompress(p.read_bytes()))

def section_records(raw):
    off=struct.unpack_from('<Q',raw,40)[0];ent,count,ni=struct.unpack_from('<HHH',raw,58)
    headers=[struct.unpack_from('<IIQQQQIIQQ',raw,off+i*ent) for i in range(count)];names=headers[ni];out={}
    for h in headers:
        p=names[4]+h[0];name=raw[p:raw.index(b'\0',p)].decode()
        out[name]={'type':h[1],'flags':h[2],'address':h[3],'offset':h[4],'bytes':h[5],'sha256':sha(raw[h[4]:h[4]+h[5]])}
    return out

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['images','original','inventory','harness','work']:ap.add_argument('--'+name,type=Path,required=True)
    a=ap.parse_args();summary=read(HERE/'SUMMARY.json');review=read(HERE/'review.json');expected=read(HERE/'MEASUREMENTS.json');members=read(HERE/'MEMBERSHIPS.json')
    require(sha(a.original.read_bytes())==summary['original_sha256'],'Original differs')
    require(sha(a.inventory.read_bytes())==summary['inventory_sha256'],'Inventory differs')
    require(sha((HERE.parent/'verify_rent_edges.py').read_bytes())==summary['parent_helper_sha256'],'Helper differs')
    for name,digest in review['harness_hashes'].items():require(sha((a.harness/name).read_bytes())==digest,'Harness differs: '+name)
    require(sha((HERE/'composition.patch').read_bytes())==summary['composition_patch_sha256'],'Patch differs')
    require(sha((HERE/'fixed-windows.ld').read_bytes())==summary['fixed_script_sha256'],'Script differs')
    a.work.mkdir(parents=True,exist_ok=False);base=a.work/'base';base.mkdir();(base/'original.so').write_bytes(a.original.read_bytes());(base/'functions.tsv').write_bytes(a.inventory.read_bytes())
    sys.path.insert(0,str(a.harness));import score,link_order
    score.BASE=base
    import target_metric,win
    windows={w['start']:w for w in score.original_windows()};require(len(windows)==1035,'Incomplete inventory');old=windows[0x5b3b0]
    old_calls,old_sys=calls(old['raw'],0x5b3b0);old_shapes=Counter((windows[c['target']]['bytes'],sha(windows[c['target']]['norm'])) for c in old_calls)
    production=gz(HERE/'PRODUCTION.json.gz');logs=gz(HERE/'LOGS.json.gz');receipts=gz(HERE/'LINK-RECEIPTS.json.gz');irs=gz(HERE/'IR.json.gz')
    rows={};sections={};negative=False
    for name,digest in summary['all_outputs'].items():
        folder=a.images/name;path=folder/'symbols.so';raw=path.read_bytes();p=production[name];launch=p['launch'];result=p['result']
        require(sha(raw)==digest and raw==(folder/'target/sbpf-solana-solana/release/deps/pump_recovered.so').read_bytes(),'Compiler output differs: '+name)
        require(result['returncode']==0 and all(v for k,v in result.items() if k.endswith('_unchanged')),'Production protection failure')
        require(launch['source_revision']==summary['source_revision'],'Source revision differs')
        for f,d in launch['source_inputs'].items():require(sha((folder/'source'/f).read_bytes())==d,'Source input differs: '+f)
        for f,d in result['logs'].items():require(sha(logs[name][f].encode())==d,'Log differs')
        require(receipts[name]['script_sha256']==summary['fixed_script_sha256'],'Wrong linker input')
        require(link_order.check_script((folder/'source/programs/pump/link/ordered.ld').read_text())['.text']==555,'Unexpected selectors')
        secs=score.sections(raw);sections[name]=section_records(raw);funcs=score.candidate_functions(path);physical={};by_address=defaultdict(set)
        for addr,size,_ in funcs:
            body=score.body(raw,secs,addr,size);shape=(size,sha(score.normalize(body,addr,secs)));physical[(addr,size)]=shape;by_address[addr].add(shape)
        hits=[f for f in funcs if '8swap_hop17h' in f[2]];require(len(hits)==1,'Ambiguous swap_hop');start,size,_=hits[0];body=score.body(raw,secs,start,size)
        refs,syscalls=calls(body,start);actual=[]
        for c in refs:
            require(len(by_address[c['target']])==1,'Ambiguous callee');actual.append(next(iter(by_address[c['target']])))
        require(len(refs)==107 and syscalls==old_sys and Counter(actual)==old_shapes,'Callee multiset or syscall differs')
        measured,scored_hash=score.score_with_hash(path);require(scored_hash==digest and set(measured)==set(windows),'Scored snapshot differs')
        found={key:sorted(addr for addr,v in measured.items() if v[key]) for key in ['normalized','raw']};require(found==members[name],'Membership differs: '+name)
        metric=json.loads(json.dumps(target_metric.measure_window(old,win.Cand(path),re.compile('8swap_hop17h'))));require(metric==[expected[name]['target']],'Target metric differs')
        span=formatter_span(score,windows,raw,secs,physical,by_address);require(span==expected[name]['formatter'],'Bound span differs')
        require(sha(body)==expected[name]['body_sha256'] and sha(score.normalize(body,start,secs))==expected[name]['normalized_body_sha256'],'Target body differs')
        if name in irs:
            ir=irs[name];require(sha(ir.encode())==expected[name]['ir_body_sha256'],'IR body differs')
            require(sha((folder/result['llvm_ir']['path']).read_bytes())==result['llvm_ir']['sha256'],'Full IR differs')
            header=ir.splitlines()[0];require(header==expected[name]['ir_header'],'IR header differs')
            require('ptr noalias nocapture noundef readonly align 8 dereferenceable(40) %h' in header,'h lost noalias')
            if name=='01-main':require('ptr noalias nocapture noundef readonly align 8 dereferenceable(144) %a' in header,'Baseline a lacks noalias')
            else:require('ptr readonly %ctx.8.val, i8 %ctx.34.val' in header,'Promoted accounts/bump differ')
        if name=='07-hints-plain':
            mutant=bytearray(body);c=refs[0];struct.pack_into('<i',mutant,c['offset']+4,-(c['offset']+8)//8)
            require(score.normalize(mutant,start,secs)==score.normalize(body,start,secs),'Negative changed normalized bytes')
            mutated,_=calls(mutant,start);altered=Counter(next(iter(by_address[c['target']])) for c in mutated)
            require(altered!=old_shapes,'Wrong callee accepted');negative=True
        rows[name]={'sha256':digest,'bytes':len(raw),'normalized':len(found['normalized']),'raw':len(found['raw']),'target':metric[0],'formatter_delta':span['delta'],'actual_callee_multiset':True,'syscall_bytes':True}
    require(negative,'Negative not run')
    require((a.images/'07-hints-plain/symbols.so').read_bytes()==(a.images/'08-hints-repeat-plain/symbols.so').read_bytes(),'Independent repeat differs')
    emit={}
    for left,right in [('01-main','06-main-plain'),('03-context-hints','07-hints-plain')]:
        x,y=sections[left],sections[right];require(x.keys()==y.keys(),'Section names differ')
        allocated=[n for n in x if x[n]['flags']&2];require(all(x[n]==y[n] for n in allocated),'Allocated bytes or metadata differ with IR emission')
        different=[n for n in x if x[n]!=y[n]];require(set(different)=={'.symtab','.strtab'},'Unexpected section differences')
        require(members[left]==members[right],'IR instrumentation changes memberships');emit[left+' -> '+right]={'allocated_sections_identical':allocated,'different_sections':different,'whole_outputs_equal':False}
    changes={}
    for left,right in [('06-main-plain','07-hints-plain'),('03-context-hints','04-context-hints-no-fee')]:
        delta={key:{'gains':sorted(set(members[right][key])-set(members[left][key])),'losses':sorted(set(members[left][key])-set(members[right][key]))} for key in ['normalized','raw']};changes[left+' -> '+right]=delta
        require(not delta['normalized']['gains'] and not delta['normalized']['losses'],'Normalized change')
        require(delta['raw']==({'gains':summary['raw_gains'],'losses':[]} if left=='06-main-plain' else {'gains':[],'losses':summary['raw_gains']}),'Unexpected raw change')
    report={'result':'PASS','images':rows,'changes':changes,'emit_comparison':emit,'whole_output_repeat':True,'wrong_callee_negative':'Rejected despite unchanged normalized body','scope':'All 1035 memberships and complete callee-body multiset; no call-order, recursive/runtime equivalence or original whole-file identity claim.'}
    (a.work/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(report,sort_keys=True))

if __name__=='__main__':main()
