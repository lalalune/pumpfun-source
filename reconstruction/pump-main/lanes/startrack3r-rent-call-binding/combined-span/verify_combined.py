#!/usr/bin/env python3
"""Read-only checks of credited source composition and emitted link-order results."""
import argparse
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import re
import struct
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from verify_rent_edges import calls,formatter_span,require,sha


def read(path):return json.loads(path.read_bytes())


def members(raw):
    require(raw.startswith(b'!<arch>\n'),'Expected ar archive')
    offset=8;names=b'';result={}
    while offset<len(raw):
        header=raw[offset:offset+60]
        require(len(header)==60 and header[-2:]==b'`\n','Invalid ar header')
        name=header[:16].decode().strip();size=int(header[48:58]);payload=raw[offset+60:offset+60+size]
        require(len(payload)==size,'Truncated ar member')
        if name=='//':names=payload
        if name.startswith('/') and name[1:].isdigit():
            start=int(name[1:]);ends=[x for x in [names.find(b'/\n',start),names.find(b'\0',start)] if x>=0]
            require(ends,'Invalid long member name');name=names[start:min(ends)].decode()
        elif name.startswith('#1/'):
            length=int(name[3:]);require(length<=size,'Invalid BSD name');name=payload[:length].rstrip(b'\0').decode();payload=payload[length:]
        if name not in ['/','//']:name=name.rstrip('/')
        require(name not in result,'Duplicate member');result[name]=payload;offset+=60+size+size%2
    require(offset==len(raw),'Truncated ar padding');return result


def bind_v3(body,start,windows,by_address):
    original,osys=calls(windows[0x80df8]['raw'],0x80df8);actual,csys=calls(body,start)
    require(len(original)==len(actual)==17 and osys==csys,'V3 call shape differs')
    for old,new in zip(original,actual):
        w=windows[old['target']]
        require(old['offset']==new['offset'] and (w['bytes'],sha(w['norm'])) in by_address[new['target']],'V3 actual callee differs')
    return len(actual)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['images','original','inventory','harness','work']:ap.add_argument('--'+name,type=Path,required=True)
    args=ap.parse_args();summary=read(HERE/'SUMMARY.json');expected=read(HERE/'MEMBERSHIPS.json');pins=read(HERE/'review.json')['harness_hashes']
    require(sha(args.original.read_bytes())==summary['original']['sha256'],'Original image differs')
    require(sha(args.inventory.read_bytes())==summary['inventory_sha256'],'Inventory differs')
    for name,digest in pins.items():require(sha((args.harness/name).read_bytes())==digest,'Harness differs: '+name)
    args.work.mkdir(parents=True,exist_ok=False);base=args.work/'base';base.mkdir()
    (base/'original.so').write_bytes(args.original.read_bytes());(base/'functions.tsv').write_bytes(args.inventory.read_bytes())
    sys.path.insert(0,str(args.harness));import score,link_order
    score.BASE=base;windows={w['start']:w for w in score.original_windows()};require(len(windows)==1035,'Incomplete windows')
    for name,digest in summary['all_outputs'].items():require(sha((args.images/name/'symbols.so').read_bytes())==digest,'Compiler output differs: '+name)
    require((args.images/'08-combined-reordered/symbols.so').read_bytes()==(args.images/'09-combined-repeat/symbols.so').read_bytes(),'Independent output repeat differs')
    images={};classes={};v3_negative=False
    rent=(windows[0x3b598]['bytes'],sha(windows[0x3b598]['norm']))
    v2=[(0x13b9b8,r'6buy_v211buy_handler17h|14pump_recovered6buy_v217h'),(0x13f630,r'6buy_v226buy_exact_quote_in_handler17h|14pump_recovered21buy_exact_quote_in_v217h'),(0x144508,r'14pump_recovered7sell_v217h')]
    for name,pin in summary['images'].items():
        path=args.images/name/'symbols.so';raw=path.read_bytes();secs=score.sections(raw);funcs=score.candidate_functions(path)
        physical={};by_address=defaultdict(set)
        for start,size,symbol in funcs:
            body=score.body(raw,secs,start,size);shape=(size,sha(score.normalize(body,start,secs)))
            physical[(start,size)]=shape;by_address[start].add(shape)
        classes[name]=Counter(physical.values())
        measured,digest=score.score_with_hash(path);require(digest==sha(raw) and set(measured)==set(windows),'Scored input differs')
        actual={key:sorted(a for a,v in measured.items() if v[key]) for key in ['normalized','raw']}
        require(actual==expected[name],'Complete membership differs: '+name)
        span=formatter_span(score,windows,raw,secs,physical,by_address)
        require(span['delta']==pin['formatter']['span_delta'],'Formatter span differs')
        row={'sha256':digest,'normalized':len(actual['normalized']),'raw':len(actual['raw']),'formatter':span,'v2_rent':{}}
        for original,pattern in v2:
            hits=[f for f in funcs if re.search(pattern,f[2])];require(len(hits)==1,'Ambiguous V2 caller')
            start,size,symbol=hits[0];body=score.body(raw,secs,start,size);old,_=calls(windows[original]['raw'],original);new,_=calls(body,start)
            indices=[i for i,c in enumerate(old) if c['target']==0x3b598];require(len(indices)==1 and len(old)==len(new),'V2 rent call shape differs')
            target=new[indices[0]]['target'];matched=rent in by_address[target]
            require(matched==('combined' in name),'V2 actual rent callee binding differs')
            row['v2_rent'][hex(original)]={'target':target,'matches_original_body':matched,'callee_shapes':[list(x) for x in sorted(by_address[target])]}
        if 'combined' in name:
            hits=[f for f in funcs if '5trade12v3_buy_costs17h' in f[2]];require(len(hits)==1,'Ambiguous V3 body')
            start,size,_=hits[0];body=score.body(raw,secs,start,size);norm=score.normalize(body,start,secs)
            require(norm==windows[0x80df8]['norm'],'V3 normalized body differs');row['v3_bound_calls']=bind_v3(body,start,windows,by_address)
            if name=='08-combined-reordered':
                mutant=bytearray(body);first=calls(body,start)[0][0];struct.pack_into('<i',mutant,first['offset']+4,-(first['offset']+8)//8)
                require(score.normalize(mutant,start,secs)==norm,'Negative fixture changed normalized body')
                try:bind_v3(mutant,start,windows,by_address)
                except ValueError:v3_negative=True
                require(v3_negative,'Wrong V3 callee accepted')
                require(span['candidate_function_count']==788 and span['delta']==40,'Unexpected final interval')
                require(len(span['missing_classes'])==len(span['extra_classes'])==7,'Residual exceeds seven bodies')
                require(sum(x['bytes']*x['count'] for x in span['missing_classes'])==112912 and sum(x['bytes']*x['count'] for x in span['extra_classes'])==112952,'Residual byte accounting differs')
        images[name]=row
    pairs=[('01-current-default','07-current-reordered'),('03-combined-default','08-combined-reordered')]
    for left,right in pairs:require(classes[left]==classes[right],'Link order changed complete normalized bodies')
    deltas={}
    for left,right in pairs+[('07-current-reordered','08-combined-reordered'),('01-current-default','08-combined-reordered'),('01-current-default','02-current-ordered')]:
        delta={key:{'gains':sorted(set(expected[right][key])-set(expected[left][key])),'losses':sorted(set(expected[left][key])-set(expected[right][key]))} for key in ['normalized','raw']}
        if right!='02-current-ordered':require(all(not item['losses'] for item in delta.values()),'Accepted comparison loses a window')
        deltas[left+' -> '+right]=delta
    require(len(deltas['01-current-default -> 08-combined-reordered']['raw']['gains'])==20,'Expected raw gains absent')
    require(deltas['07-current-reordered -> 08-combined-reordered']['normalized']['gains']==[0x80df8],'Unexpected source gain')
    archive={}
    for name,digest in summary['root_rlibs'].items():
        raw=(args.images/name/'target/sbpf-solana-solana/release/deps/libpump_recovered.rlib').read_bytes();require(sha(raw)==digest,'Root archive differs');archive[name]=members(raw)
    archives={}
    for left,right in pairs+[('08-combined-reordered','09-combined-repeat')]:
        a,b=archive[left],archive[right];require(a.keys()==b.keys(),'Archive members differ')
        changed=[n for n in a if a[n]!=b[n]];require(changed==['lib.rmeta'],'Unexpected archive member difference')
        objects=[n for n in a if n.endswith('.o')];require(len(objects)==1,'Unexpected root object count')
        archives[left+' -> '+right]={'identical_object_sha256':sha(a[objects[0]]),'metadata_equal':False}
    for label,folder in [('current','07-current-reordered'),('combined','08-combined-reordered')]:
        script=(HERE/(label+'-windows.ld')).read_bytes();require(script==(args.images/folder/'source/programs/pump/link/ordered.ld').read_bytes(),'Pinned script differs')
        link_order.check_script((HERE/(label+'-windows.ld')).read_text())
        receipt=read(args.images/folder/'link-receipt.json');require(receipt['script_sha256']==sha(script),'Link receipt differs')
    report={'result':'PASS','images':images,'memberships':deltas,'archives':archives,'whole_compiler_output_repeat':True,'wrong_callee_negative':'rejected with normalized bytes unchanged','scope':'Raw compiler outputs; normalized code/callee evidence is not whole-program identity or behavioral equivalence.'}
    (args.work/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(report,sort_keys=True))


if __name__=='__main__':main()
