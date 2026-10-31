#!/usr/bin/env python3
"""Verify historical S1-S3 causal measurements and bounded raw joins; stdlib only."""
import argparse,difflib,hashlib,io,json,re,struct,tarfile,zipfile
from pathlib import Path,PurePosixPath
from collections import Counter
SYMBOL='_ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E'
ORIGINAL='7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
COMMITS={'ECEA':'ecea7021fcb6a09959901522c6a4edca150a1a1b','S1':'66caa3e2de152190bab3d998e7f6df18243b8e1e','S2':'5cfe37b14b5486b802782651fde4a39985141494'}
ZIP_SHA={'ECEA':'e37113f971eb103ffa929a4c931f00d876bcdaef112f50ff0b6be451d788c48a','S1':'13b50791b061c72bae69ff94251bb8b26648be3bde0aac2cb423b6c352d50618','S2':'2cbef91934f7714bef0073698157f0b55210a05691178e7b32e17030992bc8c7'}
ELF_SHA={'ECEA':'8efdc872cdf169ae992c5efc193480c3cc4d9cc7b8808d956733e4f3ce713435','S1':'74ac33d132787888aa8257908750930a3537feb06acc6413d5365426dd23ff8a','S2':'eeb484325eb342fa9a59c19e661b8f8bd0af14b88b61c459946e712db253de88'}
LEAF='programs/pump/src/creator/admin_cto.rs'

def need(value,message):
    if not value: raise ValueError(message)
def sha(b): return hashlib.sha256(b).hexdigest()
def gitblob(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def js(b): return json.loads(b)
def safe(name):
    p=PurePosixPath(name);return not p.is_absolute() and '..'not in p.parts and str(p)==name

def tarbytes(raw,mode='r:*'):
    with tarfile.open(fileobj=io.BytesIO(raw),mode=mode)as t:
        mm=t.getmembers();need(len({m.name for m in mm})==len(mm),'duplicate tar path')
        need(all(m.isfile()and safe(m.name)for m in mm),'nonregular/unsafe tar member')
        return{m.name:(t.extractfile(m).read(),bool(m.mode&0o111))for m in mm}

def logical(raw):
    pos=0
    while pos<len(raw):
        n=16 if raw[pos]==0x18 else 8;need(pos+n<=len(raw),'truncated logical instruction')
        yield pos;pos+=n

def elf(b):
    need(b[:7]==b'\x7fELF\x02\x01\x01' and len(b)>=64,'ELF header')
    off=struct.unpack_from('<Q',b,40)[0];sz,count,ni=struct.unpack_from('<HHH',b,58)
    need(sz==64 and ni<count and off+sz*count<=len(b),'ELF section table')
    hh=[struct.unpack_from('<IIQQQQIIQQ',b,off+i*sz)for i in range(count)]
    def payload(h):
        need(h[4]+h[5]<=len(b),'ELF section extent');return b[h[4]:h[4]+h[5]]
    strings=payload(hh[ni]);ss={}
    for h in hh:
        need(h[0]<len(strings),'ELF name offset');end=strings.find(b'\0',h[0]);need(end>=0,'ELF name end')
        n=strings[h[0]:end].decode();need(n not in ss,'duplicate ELF section');ss[n]=(h,payload(h))
    sy=[]
    if '.symtab'in ss:
        h,d=ss['.symtab'];need(h[9]==24 and len(d)%24==0,'ELF symbol stride');st=payload(hh[h[6]])
        for i in range(0,len(d),24):
            n,info,other,sec,addr,size=struct.unpack_from('<IBBHQQ',d,i);end=st.find(b'\0',n);need(0<=n<len(st)and end>=0,'symbol name')
            sy.append((st[n:end].decode(),info,sec,addr,size))
    return ss,sy

def target(b):
    ss,sy=elf(b);f=[s for s in sy if s[0]==SYMBOL and s[1]&15==2];need(len(f)==1,'unique CTO symbol')
    x=f[0];h,t=ss['.text'];a=x[3]-h[3];z=a+x[4];bounds=set(logical(t));need(a in bounds and(z in bounds or z==len(t)),'CTO logical extent')
    return ss,sy,x,t[a:z]

def provenance(z,commit,corepayload,repo):
    members=z.namelist();need(len(members)==len(set(members))and all(safe(n)for n in members),'ZIP member domain')
    need(z.testzip()is None,'ZIP CRC');g=js(z.read('program-source-inputs.json'));core=js(z.read('toolchain-source-inputs.json'))
    need(g['base']==core['base']==commit and len(g['files'])==141 and len(core['files'])==236,'frozen provenance cohort')
    p=tarbytes(z.read('program-source.tar.gz'));need(set(p)=={x['path']for x in g['files']}and len(p)==141,'source141 domain')
    for x in g['files']:
        b,e=p[x['path']];need(len(b)==x['bytes']and sha(b)==x['sha256']and gitblob(b)==x['gitBlob']and e==(x['mode']=='100755'),'source bytes/mode '+x['path'])
    selected=js(z.read('source-inputs.json'));vector=[{'path':x['path'].removeprefix('programs/pump/'),'bytes':x['bytes'],'executable':x['mode']=='100755','sha256':x['sha256']}for x in g['files']]
    vector.sort(key=lambda x:x['path']);digest=sha(json.dumps(vector,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
    need(selected['files']==vector and selected['sha256']==digest and selected==js(z.read('preflight-builder-source-inputs.json')),'selected source vector')
    stage=js(z.read('compiled-workspace-inputs.json'));s=tarbytes(z.read('compiled-workspace.tar.gz'));need(len(s)==142 and set(s)==set(stage),'stage142 domain')
    for n,(b,e)in s.items():need(stage[n]=={'bytes':len(b),'executable':e,'sha256':sha(b)},'compiled stage bytes '+n)
    for x in core['files']:
        n=x['path'];need(safe(n),'unsafe CORE path');b=corepayload.get('core-source/'+n)
        if b is None:b=(repo/n).read_bytes()
        need(len(b)==x['bytes']and sha(b)==x['sha256']and gitblob(b)==x['gitBlob'],'CORE bytes '+n)
    pre=js(z.read('PREFLIGHT.json'));need(pre['base']==commit and(pre['programGitFiles'],pre['selectedSourceFiles'],pre['workspaceFiles'],pre['coreFiles'])==(141,141,142,236),'preflight counts')
    build=js(z.read('build.json'));need(build['ok']and build['stack_warnings']==[]and build['recipe']=='identity'and build['source_sha256']==digest,'recorded native build')
    for n,k in [('unstripped.so','unstripped_sha256'),('candidate.so','candidate_sha256')]:need(sha(z.read(n))==build[k],'build image binding')
    need(js(z.read('tool-inputs-before.json'))==js(z.read('tool-inputs-after.json')),'tool before/after')
    need(js(z.read('registry-source-inputs.json'))==js(z.read('registry-source-inputs-after.json')),'registry before/after')
    need(js(z.read('native-lld-input-before.json'))==js(z.read('native-lld-input-after.json')),'linker before/after')
    cold=js(z.read('cold-target-inputs.json'));need(cold['base']==commit and cold['sourceSha256']==digest and cold['targetAbsentBeforeBuild']and cold['dependencyTemplatesAbsent'],'cold build receipt')
    return g,core,stage,p,s,build

def graph(raw):
    """Logical instructions and direct intraprocedural CFG; calls return."""
    rows={p:struct.unpack_from('<BBhi',raw,p)for p in logical(raw)};succ={};leaders={0}
    for p,(op,reg,off,imm)in rows.items():
        nxt=p+(16 if op==0x18 else 8);s=[]
        if op==0x95:pass
        elif op&7 in(5,6)and op not in(0x85,0x8d):
            dest=p+8+off*8;need(dest in rows,'branch into noninstruction');s=[dest]
            if op not in(0x05,0x06)and nxt<len(raw):s.append(nxt)
            leaders.add(dest)
        elif nxt<len(raw):s=[nxt]
        if (op==0x95 or(op&7 in(5,6)and op not in(0x85,0x8d)))and nxt<len(raw):leaders.add(nxt)
        succ[p]=set(s)
    pred={p:set()for p in rows}
    for p,ss in succ.items():
        for q in ss:pred[q].add(p)
    starts=sorted(leaders);blocks={};owner={}
    for i,start in enumerate(starts):
        end=starts[i+1]if i+1<len(starts)else len(raw);pcs=[p for p in rows if start<=p<end]
        need(bool(pcs),'empty block');blocks[start]={'start':start,'end':end,'successors':sorted(succ[pcs[-1]]),'predecessors':[]}
        for p in pcs:owner[p]=start
    for start,block in blocks.items():
        block['successors']=sorted({owner[x]for x in block['successors']})
        block['predecessors']=sorted({owner[x]for x in pred[start]})
    return rows,succ,pred,blocks

def defines(row,reg):
    op,rr,off,imm=row
    if op in(0x85,0x8d):return reg<=5
    return (op==0x18 or op&7 in(1,4,7))and rr&15==reg

def reachdefs(rows,pred,reg,at):
    todo=list(pred[at]);seen=set();found=set()
    if at==0:found.add(None)
    while todo:
        p=todo.pop()
        if p in seen:continue
        seen.add(p)
        if defines(rows[p],reg):found.add(p)
        elif p==0:found.add(None)
        else:todo.extend(pred[p])
    return found

def reachable(edges,start):
    seen=set();todo=[start]
    while todo:
        p=todo.pop()
        if p not in seen:seen.add(p);todo.extend(edges[p])
    return seen

def fpwrite(row):
    op,reg,off,imm=row
    return(off,off+{0:4,8:2,16:1,24:8}[op&24])if op&7 in(2,3)and reg&15==10 else None

def exact(raw,expected):
    starts=set(logical(raw))
    for x in expected:
        p=x['offset'];p=int(p,0)if isinstance(p,str)else p;b=bytes.fromhex(x['raw'])
        need(p in starts and len(b)==(16 if raw[p]==0x18 else 8)and raw[p:p+len(b)]==b,'actual ELF raw witness '+hex(p))

def machine(images,w,original):
    outputs={};gg={}
    for key in('S1','S2'):
        spec=w['variants'][key];ss,sy,sym,raw=target(images[key]);need(sym[3]==141840 and sym[4]==spec['body']['bytes']and sha(raw)==spec['bodySha256'],'CTO body '+key)
        exact(raw,spec['instructions']);rows,succ,pred,blocks=graph(raw);gg[key]=(raw,rows,succ,pred)
        for expected in spec['expectedBlocks']:
            actual=blocks[expected['start']];need(actual['end']==expected['end']and set(actual['successors'])==set(expected['successors'])and set(actual['predecessors'])==set(expected['predecessors']),'actual common/selection block '+key)
        sweep=[s for s in sy if s[0]==spec['sweep']['name']and s[1]&15==2];need(len(sweep)==1 and sweep[0][3:]==(spec['sweep']['address'],9096),'outlined sweep symbol '+key)
        call=spec['sweepCall'];p=call['offset'];op,rr,off,imm=rows[p];need(op==0x85 and rr==0x10 and sym[3]+p+8+imm*8==sweep[0][3]and sym[3]+sym[4]==sweep[0][3],'actual sweep call '+key)
        outputs[key]={'CTOBytes':len(raw),'logicalInstructions':len(rows),'sweepBytes':9096,'commonSharedHeadInstructions':3}
    raw,r,succ,pred=gg['S1'];need(all(not defines(row,8)for p,row in r.items()if 0x198<p<0x3c0),'S1 shared R8 retained through delayed spill')
    need([p for p,v in r.items()if p<0xae0 and v[0]==0x79 and v[1]>>4==10 and v[2]==-1976]==[0xad0],'S1 first direct fee read after projection')
    need(len([p for p in r if 0x1270<=p<0x1288])==3,'S1 common head has three instructions')
    raw,r,succ,pred=gg['S2'];need([p for p,v in r.items()if p<0x1598 and v[0]==0x79 and v[1]>>4==10 and v[2]==-1984]==[0xb28],'S2 one bounded validation fee-tag read')
    need(reachdefs(r,pred,7,0xe50)=={0x268},'S2 creator prefix curve pointer')
    nodes=reachable(succ,0xb10)&reachable(pred,0x1568)
    ranges=[(-1432,-1425),(-1136,-1127),(-1912,-1904)]
    need(all(not any(a<hi and lo<b for lo,hi in ranges)for p in nodes if (ab:=fpwrite(r[p]))is not None for a,b in[ab]),'S2 selected direct frame ranges preserved')
    need(reachdefs(r,pred,3,0x1560)=={0x1378,0x1420,0x1468}and reachdefs(r,pred,0,0x1558)=={0xa78,0xea0,0x1410,0x1bb8}and reachdefs(r,pred,6,0x1410)=={0x1390},'S2 middle-word bounded register bridges')
    c=w['S2consumers'];exact(raw,c['final_pack']['instructions']);curve=c['curve_consumer'];exact(raw,[curve['curve_pointer_load']]+[x for pair in curve['pairs']for x in pair.values()])
    stores=[p for p,v in r.items()if (ab:=fpwrite(v))is not None and ab[0]<-1184 and -1216<ab[1]];need(stores==[0x1520,0x1530,0x1540,0x1550,0x1558,0x1560],'S2 whole-CTO direct target-store census')
    need(0x1fd8 not in reachable({p:{q for q in ss if q!=0x1520}for p,ss in succ.items()},0),'S2 pack store dominates curve read in direct CFG')
    need(all(reachdefs(r,pred,1,int(pair['curve_store']['offset'],0))=={0x1f90}for pair in curve['pairs']),'S2 curve-pointer register bridge')
    need(all(pred[int(pair['curve_store']['offset'],0)]=={int(pair['target_load']['offset'],0)}for pair in curve['pairs']),'S2 immediate curve load/store edges')
    pool=c['pool_consumer'];exact(raw,pool['target_argument']+[pool['call']]);need(pred[0x2dc0]=={0x2db8}and reachdefs(r,pred,3,0x2dd8)=={0x2dc0},'S2 pool target argument retained')
    ss,sy,_,_=target(images['S2']);found=[s for s in sy if 'cpi14admin_cto_pool17h'in s[0]and s[1]&15==2];need(len(found)==1 and found[0][3:]==(0x10a008,4056),'S2 pool helper symbol')
    p=0x2dd8;need(141840+p+8+r[p][3]*8==found[0][3],'S2 actual pool call target');h,t=ss['.text'];a=found[0][3]-h[3];helper=t[a:a+4056];exact(helper,[x for pair in pool['serialized_target_words']for x in pair.values()]);hr,hs,hp,hb=graph(helper)
    need(all(reachdefs(hr,hp,3,int(pair['target_read']['offset'],0))=={None}for pair in pool['serialized_target_words']),'S2 helper entry creator pointer reaches four reads')
    need(all(hp[int(pair['payload_store']['offset'],0)]=={int(pair['target_read']['offset'],0)}for pair in pool['serialized_target_words']),'S2 immediate pool read/store edges')
    os,_=elf(original);h,t=os['.text'];o=t[141840-h[3]:169240-h[3]]
    for x in w['originalOrder']['witnesses']:
        p=int(x['relative'],16);need(o[p:p+len(bytes.fromhex(x['raw']))].hex()==x['raw'],'original order witness')
    outputs['S1']['projectionBeforeFee']=True;outputs['S2'].update(preselectionBeforeFee=True,validationFeeTagReads=1,targetDirectStores=6,curveAndPoolConsumerJoins=True)
    return outputs

def token_metric(image,start,size):
    """Literal score.normalize/win.insns method, using this file's ELF reader."""
    ss,_=elf(image);h,text=ss['.text'];off=start-h[3];need(0<=off and off+size<=len(text),'metric body extent');raw=text[off:off+size];masked=bytearray(raw)
    for p in logical(raw):
        op,regs,disp,imm=struct.unpack_from('<BBhi',raw,p)
        if op==0x18:
            value=struct.unpack_from('<I',raw,p+4)[0]|struct.unpack_from('<I',raw,p+12)[0]<<32
            if any(h[3]>0 and h[3]<=value<h[3]+h[5]for h,data in ss.values()):masked[p+4:p+8]=bytes(4);masked[p+12:p+16]=bytes(4)
        elif op==0x85 and regs>>4==1 and imm!=-1:masked[p+4:p+8]=bytes(4)
    return raw,tuple(bytes(masked[p:p+(16 if raw[p]==0x18 else 8)])for p in logical(raw))

def mapped(instructions):
    return[{'offset':int(p,0),'raw':raw}for p,raw in instructions.items()]

def s3_native(image,w,original):
    ss,sy,sym,raw=target(image);need(sym[3:]==(141840,27400)and len(list(logical(raw)))==3337 and sha(raw)==w['bodySha256'],'S3 exact body');exact(raw,mapped(w['instructions']));r,succ,pred,blocks=graph(raw)
    need(r[8]==(0x7b,0x4a,-2296,0),'S3 incoming R4 fee tag spill')
    bound=w['prepareCall'];reads=[p for p,v in r.items()if p<bound and v[0]==0x79 and v[1]>>4==10 and v[2]==w['feeSlot']];need(reads==w['feeReads']==[0x9f8,0x1480,0x14d8],'S3 three bounded fee-tag reads')
    need(all(len(w[k])==3 for k in('feeReads','feeTests','feeNoneEntries','feeSomeEntries','preFeeStoreGroups')),'S3 complete three-arm fee/store metadata')
    writes=[p for p,v in r.items()if p<bound and(ab:=fpwrite(v))is not None and ab[0]<-2288 and -2296<ab[1]];need(writes==[8],'S3 direct fee-slot reaching store')
    for read,test,no,some in zip(reads,w['feeTests'],w['feeNoneEntries'],w['feeSomeEntries']):
        op,reg,disp,imm=r[test];need(test==read+8 and op==0x15 and reg&15==r[read][1]&15 and imm==0 and succ[test]=={no,some}and some==test+8,'S3 exact fee split')
    head=w['privateHead'];actual=blocks[head['start']];need(actual['end']==head['end']and set(actual['predecessors'])==set(head['predecessors'])=={0x1608}and set(actual['successors'])==set(head['successors']),'S3 private successful-fee block')
    no=w['noFeeHead'];actual=blocks[no['start']];need(actual['end']==no['end']and set(actual['predecessors'])==set(no['predecessors'])and set(actual['successors'])==set(no['successors']),'S3 representative fee-None shared block')
    need([p for p in r if head['start']<=p<head['end']]==[0x17c0,0x17c8,0x17d0,0x17d8]and r[0x17d0]==(0x79,0xa2,-2304,0),'S3 four-row private shared head')
    need(all(head['start']not in reachable(succ,p)for p in w['feeNoneEntries'])and all(head['start']in reachable(succ,p)for p in w['feeSomeEntries']),'S3 Some reaches private head; None cannot')
    need([p for p,v in r.items()if p<0x3c8 and defines(v,7)]==[0x100,0x190,0x198]and r[0x3c8]==(0x7b,0x7a,-2304,0),'S3 shared R7 provenance and delayed spill')
    owner=lambda p:next(start for start,b in blocks.items()if start<=p<b['end'])
    for group,read in zip(w['preFeeStoreGroups'],reads):need(len(group)==4 and all(p<read and owner(p)==owner(read)and r[p][0]==0x7b and r[p][1]&15==10 for p in group),'S3 target store arm precedes fee test in same block')
    scoped=lambda name:'pump_recovered9admin_cto8validate'in name or'pump_recovered9admin_cto7execute5sweep'in name
    need(not[s for s in sy if s[1]&15==2 and s[4]>0 and scoped(s[0])],'S3 no nonzero scoped validate/sweep symbols')
    names={}
    for name,info,sec,addr,size in sy:names.setdefault(addr,[]).append(name)
    need(not[p for p,v in r.items()if v[0]==0x8d]and not[p for p,v in r.items()if v[0]==0x85 and v[1]>>4==1 and any(scoped(n)for n in names.get(141840+p+8+v[3]*8,[]))],'S3 no scoped outline or CALLX witness')
    c=w['consumerWitnesses'];exact(raw,mapped(c['targetWrites']));exact(raw,mapped(c['curvePairs']));exact(raw,mapped(c['pool']['caller']));exact(raw,mapped(c['sharingAssembly']));exact(raw,mapped(c['sharing']['caller']))
    lo,hi=c['targetFrame'];stores=[p for p,v in r.items()if(ab:=fpwrite(v))is not None and ab[0]<hi and lo<ab[1]];need(stores==sorted(int(p,0)for p in c['targetWrites']),'S3 selected target direct-store census')
    need(c['targetFrame']==[-1376,-1344]and c['sharingFrame']==[-1588,-1555],'S3 distinct outgoing argument buffers')
    for label,callpc,argpc,argprev in [('pool',0x51f8,0x51e0,0x51d8),('sharing',0x4e38,0x4e30,0x4e28)]:
        item=c[label];addr=int(item['address'],0)if isinstance(item['address'],str)else item['address'];needle='cpi14admin_cto_pool17h'if label=='pool'else'cpi24admin_cto_sharing_config17h';found=[s for s in sy if s[1]&15==2 and needle in s[0]];need(len(found)==1 and found[0][3:]==(addr,item['bytes'])and r[callpc][0]==0x85 and r[callpc][1]>>4==1 and 141840+callpc+8+r[callpc][3]*8==addr,'S3 actual consumer call '+label)
        need(pred[argpc]=={argprev}and reachdefs(r,pred,3,callpc)=={argpc},'S3 outgoing argument register bridge '+label);h,text=ss['.text'];a=addr-h[3];helper=text[a:a+item['bytes']];need(sha(helper)==item['sha256'],'S3 helper body '+label);exact(helper,mapped(item['serializer']))
    os,_=elf(original);h,text=os['.text'];old=text[141840-h[3]:169240-h[3]]
    families=w['originalFamilyCorrection']['families'];need([x['name']for x in families]==['Validated nonholder target reconstruction','Post-fee shared-nonholder input payload transport','Post-flags selected target outer pack and true use']and all(x['instructions']for x in families),'S3 complete distinct original copy-family witnesses')
    for family in families:exact(old,mapped(family['instructions']))
    return{'CTOBytes':27400,'logicalInstructions':3337,'validationFeeTagReads':3,'privateFeeSomeSharedHead':True,'noScopedOutlineOrCALLXWitness':True,'preFeeTargetStoreArms':3,'distinctTargetAndSharingArgumentBuffers':True,'consumerScope':'Selected raw points/direct target-store census/outgoing register bridges and serializer bytes; not full bytewise or opaque-callee alias analysis.','originalFamilies':'Selected-target transport and separate late entry-new/sharing transport remain distinct; no Result/Try type inference.'}

def s3_extension(here,repo,olddata,oldprov,original):
    m=js((here/'s3-inputs.json').read_bytes());commits={'13fe':'13fe4536be64d8c5c10f8905e9d2236f423ac4f4','S3':'65f0162a3dcd381df0f831082dd6732c9af4ab78'};need(m['commits']==commits,'S3 source cohorts')
    pins={'13fe':'875edcd6e9ebb7e5b8fb2495d0008e723762b1f0251a02e038881fb56749fa92','S3':'0f1a82695dd41525fffbebe667c3067062a9a1fd1fd3fb4b70cbdb054965bdda'};elfpins={'13fe':'cec841bd60cc002213829e3149e7c170dbb7f5bbc47a9887cef1ab7e0193319e','S3':'100d222047a2281a4409d8f732266955368504479d3d4076b4f6e3af08ef37e4'}
    archive=(here/m['archive']['path']).read_bytes();need(sha(archive)==m['archive']['sha256']and len(archive)==m['archive']['bytes'],'S3 normal archive');packed=tarbytes(archive);need(set(packed)==set(m['archive']['members'])and set(packed).isdisjoint(olddata),'S3 normal member domain');data={n:b for n,(b,e)in packed.items()}
    for n,b in data.items():need(m['archive']['members'][n]=={'bytes':len(b),'sha256':sha(b)},'S3 archive member '+n)
    z={};prov={};images={};scores={};sources={}
    for key,commit in commits.items():
        raw=data['raw/'+key+'.zip'];count=43 if key=='13fe'else 45;need(sha(raw)==pins[key]and m['rawArchives'][key]=={'member':'raw/'+key+'.zip','sha256':sha(raw),'members':count},'S3 exact raw ZIP '+key);z[key]=zipfile.ZipFile(io.BytesIO(raw));need(len(z[key].namelist())==count,'S3 raw ZIP count')
        prov[key]=provenance(z[key],commit,olddata,repo);need(prov[key][1]['files']==oldprov['ECEA'][1]['files'],'S3 same recorded CORE236 bytes/modes');images[key]=z[key].read('unstripped.so');need(sha(images[key])==elfpins[key],'S3 exact ELF '+key);scores[key]=js(z[key].read('score.json'));sources[key]=prov[key][3][LEAF][0]
        c=data['git/'+key+'.commit'];need(hashlib.sha1(b'commit '+str(len(c)).encode()+b'\0'+c).hexdigest()==commit,'S3 commit object');parents=[x[7:]for x in c.decode().splitlines()if x.startswith('parent ')];need(parents==(['963d1eefbed3a81a51d2d52f80026c5434a7a423']if key=='13fe'else[commits['13fe']]),'S3 exact source parent')
        modes={'source':dict(Counter(x['mode']for x in prov[key][0]['files'])),'CORE':dict(Counter(x['mode']for x in prov[key][1]['files']))};need(modes==m['recordedModes'][key],'S3 recorded source/CORE modes')
        root=js(data['receipts/'+key+'-root-admission.json']);need(root['base']==commit and root['images']['unstripped.so']==elfpins[key]and root['sourceSha256']==prov[key][5]['source_sha256']and root['sourceAndArchiveAdmission']==root['independentOfficialScorer']=='PASS','S3 retained root admission')
        result=js(z[key].read('RESULT.json'));need('FAILURE.json'not in z[key].namelist()and result['base']==commit and result['sourceUnchanged']and result['registrySourceUnchanged']and result['toolInputsUnchanged']and result['coldTarget']and result['unstrippedSha256']==elfpins[key],'S3 native RESULT success retained')
        ww=scores[key]['windows'];summary=scores[key]['summary'];need(len(ww)==1035 and summary['candidate_sha256']==elfpins[key]and summary['total']==1035 and(sum(x['normalized']for x in ww.values()),sum(x['raw']for x in ww.values()))==(1034,1034),'S3 saved membership totals')
    ref=js(z['S3'].read('reference-admission.json'));need(ref['base']==commits['13fe']and ref['run']==41170683278 and ref['artifactId']==13031166975 and ref['originalZipSha256']==pins['13fe']and ref['coreEqual']and set(ref['files'])==set(z['13fe'].namelist()),'S3 exact control reference')
    for n,e in ref['files'].items():
        b=z['13fe'].read(n);need(e=={'bytes':len(b),'sha256':sha(b)},'S3 reference member '+n)
    need(scores['13fe']['windows']==scores['S3']['windows'],'S3 all saved membership rows unchanged');comparison=js(z['S3'].read('CANDIDATE-COMPARISON.json'));need(comparison['changedRows']=={}and comparison['allRowsEqual']and comparison['fullRowsCompared']==1035 and comparison['noRawLosses']and comparison['noNormalizedLosses'],'S3 saved no-loss success comparison')
    need([sha(sources[k])for k in commits]==['50ce2f82dacecc11ccc4b67409c21a5325cfdc3fc48a6e28cc322e06473ca715','32d4d71065f96e0d24f65ead880974a4e4cc95919ec2ef0bc113a0d536e3d7b9']and m['sourceSHA256']=={k:sha(v)for k,v in sources.items()},'S3 exact source leaves');a,b=(sources[k].decode().splitlines(True)for k in commits);need(len(a)==len(b)==772 and[i+1 for i,(x,y)in enumerate(zip(a,b))if x!=y]==[283,312,339],'S3 three-line source delta')
    patch=''.join(difflib.unified_diff(a,b,fromfile='a/'+LEAF,tofile='b/'+LEAF)).encode();need(patch==(here/m['patch']['path']).read_bytes()and m['patch']=={'path':'13fe-to-S3.patch','bytes':len(patch),'sha256':sha(patch)},'S3 exact source patch');need(a[333]==b[333]and a[337]==b[337]and a[339:]==b[339:]and'(false,Some(new),true)'in b[338]and'Ok((holder,cashback,target,sharing_update,collect_old,skip))'in b[338],'S3 two volatile sites/downstream tail/original new settings payload')
    need(set(prov['13fe'][2])==set(prov['S3'][2])and[n for n in prov['13fe'][2]if prov['13fe'][2][n]!=prov['S3'][2][n]]==[LEAF],'S3 sole staged source delta')
    for field in('witnesses','metric'):
        item=m[field];raw=(here/item['path']).read_bytes();need(len(raw)==item['bytes']and sha(raw)==item['sha256'],'S3 declaration '+field)
    w=js((here/m['witnesses']['path']).read_bytes());metric=js((here/m['metric']['path']).read_bytes());need(w['ELFSha256']==elfpins['S3']and sha(olddata[w['originalFamilyCorrection']['sourceReceiptInOldArchive']])==w['originalFamilyCorrection']['sourceReceiptSha256'],'S3 witness/original family source binding')
    cached=data[metric['cachedReceiptMember']];need(sha(cached)==metric['cachedReceiptSha256']=='2ab39d249030560c5a2dc9bcc98d47c3f463ea3ed69e81b507394af73783c045','S3 cached metric receipt')
    expected={'win.py':'658cd1b0b7d8fa615e8e986843d1bb597a48d3626e05e0508fba7e651eb50c71','score.py':'5640d87864c6bc57005b8ada86f82dd1c944c92f5edf5181de4bb5e7568063f5','score_admission.py':'2d79d738d3a5ec17b3affe1f3e49aa077752f45260dc8b758c915cae1c96d088','instruction_stream.py':'288c9ceb3f0f177688501922ce56e6a72fe9c3fedcddf9ad1de474412f61ef9d','elf_symbols.py':'7bae771bbc9039a595e84c956500268b2601d2f97a93b3edcc83fbc348a9a74c'};need(metric['methodFiles']==expected,'S3 pinned metric algorithm versions')
    for name,digest in expected.items():need(sha(olddata['core-source/reconstruction/harness/'+name])==digest,'S3 archived method '+name)
    need(metric['original']['elfSha256']==ORIGINAL and all(metric['candidates'][k]['elfSha256']==elfpins[k]for k in commits)and metric['nativeNoLoss']=='SUCCESS'and metric['VMExecutions']==0,'S3 metric source/outcome declarations')
    oraw,ot=token_metric(original,141840,27400);need(sha(oraw)==metric['original']['bodySha256']and len(ot)==3339,'S3 metric original body/tokens');results={}
    for key in commits:
        spec=metric['candidates'][key];_,_,sym,_=target(images[key]);raw,tokens=token_metric(images[key],sym[3],sym[4]);need(sym[3:]==(141840,27400)and sha(raw)==spec['bodySha256']and len(tokens)==spec['logicalInstructions']==3337,'S3 metric candidate body/tokens');matching=sum(x.size for x in difflib.SequenceMatcher(None,ot,tokens,autojunk=False).get_matching_blocks());ratio=2*matching/(len(ot)+len(tokens));need(matching==spec['normalizedMatchingLogicalInstructionsM']and ratio==spec['maintainedWinNormalizedRatio'],'S3 exact maintained target metric');results[key]={'normalizedM':matching,'ratio':ratio}
    need(results['13fe']['normalizedM']==2245 and results['S3']['normalizedM']==1279 and results['S3']['normalizedM']-results['13fe']['normalizedM']==metric['deltaNormalizedM']==-966 and metric['sourceDecision']=='REJECTED_TARGET_METRIC','S3 target regression/source rejection')
    held=data[m['held']['member']];need(sha(held)==m['held']['sha256'],'S3 held receipt');held=js(held);need(held['source']==commits['S3']and held['VM_executions']==0 and not held['private_snapshot_created']and not held['runner_started']and held['root_hold_honored'],'S3 VM held before launch')
    need(not m['diagnostic']['publicTraceIncluded']and not m['diagnostic']['publicReplayClaim']and m['diagnostic']['controlELFSha256']==elfpins['13fe']and m['diagnostic']['S3ELFSha256']==elfpins['S3'],'S3 omitted private diagnostic is not replayed')
    return{'cohorts':commits,'nativeNoLoss':'SUCCESS','savedMembershipRowsUnchanged':1035,'normalizedAndRawMembershipMatches':1034,'sourceDecision':'REJECTED_TARGET_METRIC','targetMetric':results,'deltaNormalizedM':-966,'recordedVMExecutions':0,'native':s3_native(images['S3'],w,original),'diagnostic':'PRIVATE_PENDING_NOT_INCLUDED_OR_REPLAYED','limits':'Different controls from S1/S2. Target-token similarity is not matched-window membership. No Rust tuple/Result niche, current-main gain, runtime, generic alias analysis or omitted diagnostic replay claim.'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--repo',type=Path);args=ap.parse_args();here=Path(__file__).resolve().parent
    repo=args.repo.resolve()if args.repo else next((q for q in here.parents if(q/'evidence/original/pump/deployed.so').is_file()),None);need(repo is not None,'provide --repo with checked-in original and pinned binary CORE inputs')
    m=js((here/'inputs.json').read_bytes());need(m['commits']==COMMITS,'source cohort');archive=(here/m['archive']['path']).read_bytes();need(sha(archive)==m['archive']['sha256']and len(archive)==m['archive']['bytes'],'sealed archive')
    packed=tarbytes(archive);need(set(packed)==set(m['archive']['members']),'outer archive domain');data={n:b for n,(b,e)in packed.items()}
    for n,b in data.items():need(m['archive']['members'][n]=={'bytes':len(b),'sha256':sha(b)},'outer member '+n)
    original=(repo/'evidence/original/pump/deployed.so').read_bytes();need(sha(original)==ORIGINAL,'checked-in original image')
    wraw=(here/'witnesses.json').read_bytes();need(m['witnesses']=={'bytes':len(wraw),'sha256':sha(wraw)},'witness identity');w=js(wraw)
    z={};prov={};images={};score={}
    for key,commit in COMMITS.items():
        raw=data['raw/'+key+'.zip'];count=43 if key=='ECEA'else 45;need(sha(raw)==ZIP_SHA[key]and m['rawArchives'][key]=={'member':'raw/'+key+'.zip','sha256':sha(raw),'members':count},'raw ZIP identity '+key)
        z[key]=zipfile.ZipFile(io.BytesIO(raw));need(len(z[key].namelist())==count,'raw ZIP census');prov[key]=provenance(z[key],commit,data,repo)
        images[key]=z[key].read('unstripped.so');need(sha(images[key])==ELF_SHA[key],'unstripped identity '+key);score[key]=js(z[key].read('score.json'))
        c=data['git/'+key+'.commit'];need(hashlib.sha1(b'commit '+str(len(c)).encode()+b'\0'+c).hexdigest()==commit,'source commit object '+key)
        if key!='ECEA':need([x[7:]for x in c.decode().splitlines()if x.startswith('parent ')]==[COMMITS['ECEA']],'candidate sole ECEA parent')
        root=js(data['receipts/'+key+'-root-admission.json']);need(root['base']==commit and root['images']['unstripped.so']==ELF_SHA[key]and root['images']['candidate.so']==prov[key][5]['candidate_sha256']and root['sourceAndArchiveAdmission']=='PASS'and root['independentOfficialScorer']=='PASS','retained root admission binding')
    need(all(prov[k][1]['files']==prov['ECEA'][1]['files']for k in COMMITS),'same CORE236')
    cp={n.removeprefix('core-source/')for n in data if n.startswith('core-source/')};allcore={x['path']for x in prov['ECEA'][1]['files']};need(cp==set(m['coreArchivedPaths'])and allcore-cp==set(m['coreExternalBinaryPaths']),'CORE storage domain')
    source={k:prov[k][3][LEAF][0]for k in COMMITS};need([sha(source[k])for k in COMMITS]==['6acfd4b38634ab18c877d7868e9a54bb167c17f465334dfa24996b78910c93b3','7bd0a55d1f9205ccbe45e5bfea4f02556d020674b0e1d8faae41bae04a9cc778','655abec1538697c255f3c1841c3827159b3d92094afe13aa961bcd3f40910689'],'exact CTO source leaves')
    lines={k:b.decode().splitlines(True)for k,b in source.items()};need(all(len(x)==772 for x in lines.values()),'772 source coordinates')
    errors=lambda ls:[(i+1,m.group(1))for i,x in enumerate(ls)for m in re.finditer(r'error!\(PumpError::([A-Za-z0-9_]+)\)',x)]
    need(errors(lines['ECEA'])==errors(lines['S1'])==errors(lines['S2']),'error macro coordinates')
    for old,new,name in [('ECEA','S1','ECEA-to-S1.patch'),('S1','S2','S1-to-S2.patch')]:
        a,b=prov[old][2],prov[new][2];need(set(a)==set(b)and[n for n in a if a[n]!=b[n]]==[LEAF],'sole staged source delta')
        patch=''.join(difflib.unified_diff(lines[old],lines[new],fromfile='a/'+LEAF,tofile='b/'+LEAF)).encode();need(patch==(here/name).read_bytes()and m['patches'][name]=={'bytes':len(patch),'sha256':sha(patch)},'exact source content patch')
    a,b,c=lines['ECEA'],lines['S1'],lines['S2'];need([i+1 for i,(x,y)in enumerate(zip(a,b))if x!=y]==[314,315,334,338,339]and[i+1 for i,(x,y)in enumerate(zip(b,c))if x!=y]==[315,339],'bounded source deltas')
    need(a[:313]==b[:313]==c[:313]and b[313]==' Ok(target)}\n','creator helper signature/checks retained')
    marker='let (collect_old,sharing_update,skip)=';head,tail=a[338].split(marker,1);need(b[314]==head.removeprefix(' Ok(target)}')+'\n'and b[338]==marker+tail,'S1 Result split and late override')
    need(c[314]==b[314].removesuffix('\n')+'if shared&&!holder{target=st.creator;}\n'and c[338]==b[338].replace('target=a.bonding_curve.creator;',''),'S2 early selection only')
    oldcast='holder_key as *const Pubkey as *const u8';newcast='&holder_key as *const Pubkey as *const u8'
    need(all(b[n-1].replace(newcast,oldcast)==a[n-1]and c[n-1]==b[n-1]for n in range(326,339)),'fee guards and both volatile reads preserved')
    need([i+1 for i,x in enumerate(c)if 'read_volatile'in x]==[334,338]and a[339:]==b[339:]==c[339:],'volatile coordinates and downstream tail')
    base=score['ECEA']['windows'];need(len(base)==1035 and(sum(x['normalized']for x in base.values()),sum(x['raw']for x in base.values()))==(1034,1034),'saved control totals')
    need('RESULT.json'in z['ECEA'].namelist()and'FAILURE.json'not in z['ECEA'].namelist(),'control receipt')
    negatives={}
    for key in('S1','S2'):
        ref=js(z[key].read('reference-admission.json'));need(ref['base']==COMMITS['ECEA']and ref['run']==41166161483 and ref['artifactId']==13029328269 and ref['originalZipSha256']==ZIP_SHA['ECEA']and ref['coreEqual'],'exact native reference')
        need(set(ref['files'])==set(z['ECEA'].namelist()),'reference43 domain')
        for n,e in ref['files'].items():
            b=z['ECEA'].read(n);need(e=={'bytes':len(b),'sha256':sha(b)},'reference member '+n)
        ww=score[key]['windows'];need(set(ww)==set(base)and all(base[n]['normalized']==ww[n]['normalized']for n in base),'saved normalized equality')
        losses=[n for n in base if base[n]['raw']and not ww[n]['raw']];need(len(losses)==687 and(sum(x['normalized']for x in ww.values()),sum(x['raw']for x in ww.values()))==(1034,347),'saved rejection arithmetic')
        summary=score[key]['summary'];need(sorted(summary['raw_losses'],key=lambda n:int(n,0))==[hex(n)for n in sorted(map(int,losses))],'saved loss declaration')
        changed={n:{'reference':base[n],'candidate':ww[n]}for n in base if base[n]!=ww[n]};cmp=js(z[key].read('CANDIDATE-COMPARISON.json'));need(cmp['changedRows']==changed and cmp['noNormalizedLosses']and not cmp['noRawLosses'],'saved rejecting comparison')
        fail=js(z[key].read('FAILURE.json'));need(fail['base']==COMMITS[key]and fail['type']=='ValueError'and'raw or normalized losses'in fail['message']and'RESULT.json'not in z[key].namelist(),'original native failure retained')
        negatives[key]={'nativeConclusion':'FAIL/no-loss guard','normalized':1034,'raw':347,'rawLosses':687,'buildSeconds':prov[key][5]['seconds']}
    for key in COMMITS:
        ww=score[key]['windows'];summary=score[key]['summary'];need(summary['candidate_sha256']==ELF_SHA[key]and summary['total']==len(ww)and summary['normalized']==sum(x['normalized']for x in ww.values())and summary['raw']==sum(x['raw']for x in ww.values()),'saved summary recomputation')
    findings=data['prior/FINDINGS.json'];need(sha(findings)=='261968890255a52b0cb1887fe039c0afd8940abeb0290a75268e86be22bfcf74','corrected exact prior receipt')
    for x in js(findings)['authenticated_retained_files']:
        b=data['prior/'+x['retained_text']];need(len(b)==x['bytes']and sha(b)==x['sha256']and gitblob(b)==x['git_blob'],'retained prior script/text')
    need(data['analysis/unqualified/S1-ABI.json']==b''and all(n in data for n in m['unqualified']),'empty/failed ABI evidence retained and unqualified')
    result={'status':'PASS_HISTORICAL_S1_S2_NEGATIVES_PRESERVED','commits':COMMITS,'sourceFiles':141,'stageFiles':142,'COREFiles':236,'negativeMeasurements':negatives,'machine':machine(images,w,original),'prior3384':'Exact execute-side fee-helper negative credited; reported old-base result, not replayed.','limits':'Recorded score arithmetic and selected actual raw/CFG/direct-frame/register/consumer joins only. Normally returning calls and private-buffer nonalias assumption. No compile, IR, VM, official scorer, Rust lifetime/type/whole-ABI equivalence, exterior-address-only theorem, latest-main executable qualification, source gain or followup source authorization.'}
    result['S3Extension']=s3_extension(here,repo,data,prov,original);result['status']='PASS_HISTORICAL_S1_S2_S3_CAUSAL_EVIDENCE_PRESERVED'
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()

