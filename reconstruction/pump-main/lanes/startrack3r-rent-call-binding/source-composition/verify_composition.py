#!/usr/bin/env python3
"""Offline verification of pinned source-composition compiler outputs; executes no targets."""
import argparse,gzip,json,struct,sys
from collections import Counter,defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from verify_rent_edges import calls,formatter_span,require,sha

def read(p):return json.loads(p.read_bytes())
def gunzip(p):return json.loads(gzip.decompress(p.read_bytes()))

def bindings(body,start,original,windows,by_address):
    old,old_sys=calls(windows[original]['raw'],original);new,new_sys=calls(body,start)
    require(len(old)==len(new) and old_sys==new_sys,'Call shape or syscall bytes differ')
    mismatches=[]
    for i,(a,b) in enumerate(zip(old,new)):
        shape=(windows[a['target']]['bytes'],sha(windows[a['target']]['norm']))
        if a['offset']!=b['offset'] or shape not in by_address[b['target']]:mismatches.append(i)
    return {'direct_calls':len(old),'syscalls':len(old_sys),'mismatch_ordinals':mismatches}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['images','original','inventory','harness','work']:ap.add_argument('--'+name,type=Path,required=True)
    args=ap.parse_args();summary=read(HERE/'SUMMARY.json');expected=read(HERE/'MEMBERSHIPS.json');review=read(HERE/'review.json')
    require(sha(args.original.read_bytes())==summary['original']['sha256'],'Original differs');require(sha(args.inventory.read_bytes())==summary['inventory_sha256'],'Inventory differs')
    for name,digest in review['harness_hashes'].items():require(sha((args.harness/name).read_bytes())==digest,'Harness differs: '+name)
    require(sha((HERE/'composition.patch').read_bytes())==summary['composition_patch_sha256'],'Source patch differs')
    args.work.mkdir(parents=True,exist_ok=False);base=args.work/'base';base.mkdir();(base/'original.so').write_bytes(args.original.read_bytes());(base/'functions.tsv').write_bytes(args.inventory.read_bytes())
    sys.path.insert(0,str(args.harness));import score,link_order
    score.BASE=base;windows={w['start']:w for w in score.original_windows()};require(len(windows)==1035,'Incomplete original inventory')
    production=gunzip(HERE/'PRODUCTION.json.gz');logs=gunzip(HERE/'LOGS.json.gz');receipts=gunzip(HERE/'LINK-RECEIPTS.json.gz')
    for name,digest in summary['all_outputs'].items():
        raw=(args.images/name/'symbols.so').read_bytes();require(sha(raw)==digest,'Output differs: '+name)
        require(raw==(args.images/name/'target/sbpf-solana-solana/release/deps/pump_recovered.so').read_bytes(),'Copied output differs from retained compiler destination')
        p=production[name];require(p['result']['returncode']==0 and all(v for k,v in p['result'].items() if k.endswith('_unchanged')),'Failed production/protection checks')
        for log,d in p['result']['logs'].items():require(sha(logs[name][log].encode())==d,'Compiler log differs')
        script=args.images/name/'source/programs/pump/link/ordered.ld';require(sha(script.read_bytes())==receipts[name]['script_sha256'],'Actual linker script differs');link_order.check_script(script.read_text())
    require((args.images/'04-composed-ordered/symbols.so').read_bytes()==(args.images/'05-composed-repeat/symbols.so').read_bytes(),'Whole compiler repeat differs')
    images={};classes={};negative=False
    for name,pin in summary['images'].items():
        path=args.images/name/'symbols.so';raw=path.read_bytes();sections=score.sections(raw);funcs=score.candidate_functions(path);physical={};by_address=defaultdict(set);bodies={}
        for a,n,_ in funcs:
            body=score.body(raw,sections,a,n);shape=(n,sha(score.normalize(body,a,sections)));physical[(a,n)]=shape;by_address[a].add(shape);bodies[(a,n)]=body
        classes[name]=Counter(physical.values());measured,digest=score.score_with_hash(path)
        require(digest==sha(raw) and set(measured)==set(windows),'Scored data differs')
        member={key:sorted(a for a,v in measured.items() if v[key]) for key in ['normalized','raw']};require(member==expected[name],'Complete membership differs: '+name)
        span=formatter_span(score,windows,raw,sections,physical,by_address);require(span['delta']==pin['formatter']['span_delta'],'Bound span differs')
        row={'sha256':digest,'normalized':len(member['normalized']),'raw':len(member['raw']),'formatter':span,'calls':{}}
        for original in [0x72810,0x80df8,0x13b9b8,0x13f630,0x144508]:
            hits=[(a,n) for (a,n),shape in physical.items() if shape==(windows[original]['bytes'],sha(windows[original]['norm']))]
            composed='composed' in name;matched=composed or original not in [0x72810,0x13b9b8]
            require(len(hits)==int(matched),'Unexpected complete normalized body matches')
            if not hits:continue
            a,n=hits[0];body=bodies[(a,n)];bound=bindings(body,a,original,windows,by_address)
            wanted=[] if composed or original==0x80df8 else [95] if original==0x13f630 else [56]
            require(bound['mismatch_ordinals']==wanted,'Actual callees differ from expected')
            row['calls'][hex(original)]={'start':hex(a),**bound}
            if name=='04-composed-ordered' and original==0x13b9b8:
                refs,_=calls(body,a);call=refs[55];mutant=bytearray(body);struct.pack_into('<i',mutant,call['offset']+4,-(call['offset']+8)//8)
                require(score.normalize(mutant,a,sections)==score.normalize(body,a,sections),'Negative changed normalized bytes')
                require(bindings(mutant,a,original,windows,by_address)['mismatch_ordinals']==[55],'Wrong rent callee accepted');negative=True
        if name=='04-composed-ordered':
            require(span['candidate_function_count']==788 and span['delta']==-96,'Unexpected final interval')
            require(len(span['missing_classes'])==len(span['extra_classes'])==4,'Unexpected residual class count')
            require(sum(x['bytes']*x['count'] for x in span['missing_classes'])==69416 and sum(x['bytes']*x['count'] for x in span['extra_classes'])==69320,'Residual accounting differs')
            require(sum(x['direct_calls'] for x in row['calls'].values())==354,'Incomplete callee audit')
        images[name]=row
    require(negative,'Negative fixture not exercised')
    for a,b in [('01-main-map','02-main-ordered'),('06-composed-map','04-composed-ordered')]:require(classes[a]==classes[b],'Link-only variants changed normalized physical bodies')
    changes={}
    for a,b in [('01-main-map','06-composed-map'),('02-main-ordered','04-composed-ordered')]:
        changes[a+' -> '+b]={key:{'gains':sorted(set(expected[b][key])-set(expected[a][key])),'losses':sorted(set(expected[a][key])-set(expected[b][key]))} for key in ['normalized','raw']}
        d=changes[a+' -> '+b];require(not d['normalized']['losses'] and not d['raw']['losses'],'Lost baseline memberships')
        require(d['normalized']['gains']==[0x72810,0x13b9b8] and len(d['raw']['gains'])==42,'Unexpected source-composition gains')
    report={'result':'PASS','images':images,'changes':changes,'whole_output_repeat':True,'wrong_callee_negative':'Rejected while normalized bytes remain equal','scope':'Complete static body/call checks; no recursive/runtime equivalence or whole-original raw identity.'}
    (args.work/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(report,sort_keys=True))

if __name__=='__main__':main()
