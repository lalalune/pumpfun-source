#!/usr/bin/env python3
"""Verify one frozen negative build pair; stdlib reads only, no scorer/toolchain."""
import argparse,difflib,hashlib,io,json,struct,tarfile,zipfile
from collections import Counter
from pathlib import Path,PurePosixPath

CONTROL='39eb377aa6c6ce4aacff273aa13732abb0c0078a'
CANDIDATE='0fc50efbc599fa1e025169c8db06fceb25c9c192'
SYMBOL='_ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E'
ORIGINAL='7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
ZIP_SHA={'control':'94d7f23a92e0cae60b186ae589bffa7767e2c18f63b93dfb8e97f6c7e4a912c6','c1':'081b9de25c3c6ed446b3b3d610d08f8d58a0a6e88f7fea16b9aab0a3fc341477'}
ELF_SHA={'control':'289b7d63122fb1f8a64213df1b781b49aa596448e2f33256fa85365d9f7ed4f4','c1':'04e315f4b9aadaa3754d561ddbee82db10793eee55c33fea3e720d951b0b168e'}
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

def exterior(old,new):
    os,oy,ot,ob=target(old);ns,ny,nt,nb=target(new);need(ot[3:]==(141840,27400)and nt[3:]==(141840,27616),'target extent change')
    delta=nt[4]-ot[4];oldend=ot[3]+ot[4];textva=os['.text'][0][3];a=os['.text'][1];b=ns['.text'][1]
    need(len(b)-len(a)==delta==216 and os['.rodata'][1]==ns['.rodata'][1],'text/rodata extent')
    for n,(h,d)in os.items():
        if h[2]&2:need(ns[n][0][3]-h[3]==(0 if n=='.text'else delta),'allocated section address '+n)
    af={s[0]:s for s in ny if s[1]&15==2};bf={s[0]:s for s in oy if s[1]&15==2}
    need(set(af)==set(bf)and len(af)==1060,'named function domain');need([n for n in af if af[n][4]!=bf[n][4]]==[SYMBOL],'only CTO named size change')
    shifts=Counter(af[n][3]-bf[n][3]for n in af);need(shifts=={0:156,216:904},'named function address shifts')
    shifted=lambda address:address+(delta if address>=oldend else 0)
    count=Counter();starts=set(logical(a));nstarts=set(logical(b))
    for pos in range(0,len(a),8):
        va=textva+pos
        if ot[3]<=va<oldend:continue
        nv=shifted(va);np=nv-textva;x=a[pos:pos+8];y=b[np:np+8]
        if x==y:continue
        op,reg,off,imm=struct.unpack('<BBhi',x);op2,reg2,off2,imm2=struct.unpack('<BBhi',y)
        need(pos in starts and np in nstarts and(op,reg,off)==(op2,reg2,off2),'exterior opcode/register/offset')
        if op==0x85 and reg==0x10:
            dest=va+8+imm*8;need(not ot[3]<dest<oldend and nv+8+imm2*8==shifted(dest),'bound exterior call target');count['callImmediateDelta'+str(imm2-imm)]+=1
        elif op==0x18:
            ptr=struct.unpack_from('<I',a,pos+4)[0]|struct.unpack_from('<I',a,pos+12)[0]<<32;ptr2=struct.unpack_from('<I',b,np+4)[0]|struct.unpack_from('<I',b,np+12)[0]<<32
            names=[n for n,(h,d)in os.items()if h[2]&2 and h[3]<=ptr<h[3]+h[5]]
            need(len(names)==1 and ptr2==shifted(ptr),'bound exterior lddw');h=os[names[0]][0];nh=ns[names[0]][0];need(nh[3]<=ptr2<nh[3]+nh[5]and ptr2-nh[3]-(ptr-h[3])==((delta if ptr>=oldend else 0)if names[0]=='.text'else 0),'same section with qualified insertion offset');count['lddwAddressDelta216']+=1
        else:raise ValueError('unexpected exterior changed bytes')
    expected={'lddwAddressDelta216':5196,'callImmediateDelta27':827,'callImmediateDelta-27':2143};need(count==expected,'full exterior change census')
    return{'CTOBytes':[len(ob),len(nb)],'CTOLogicalInstructions':[len(list(logical(ob))),len(list(logical(nb)))],'textGrowth':delta,'functionAddressDeltas':dict(shifts),'fullExteriorTextChanges':dict(count)}

def rawproof(old,new,original):
    def rows(raw):return{p:struct.unpack_from('<BBhi',raw,p)for p in logical(raw)}
    _,_,_,a=target(old);_,_,_,b=target(new);ss,_=elf(original);h,t=ss['.text'];o=t[141840-h[3]:169240-h[3]];r,c,g=rows(a),rows(b),rows(o)
    def edge(p,q):need(c[p][0]&7 in(5,6)and p+8+c[p][2]*8==q,'C1 exact branch '+hex(p))
    for p,q in[(0xa60,0xe00),(0x19d8,0x1a88),(0x1bc0,0x1d68),(0x1d88,0x1d98),(0x1d90,0xa70),(0x19f8,0x1d98),(0x1de0,0xa70),(0xac8,0xad8)]:edge(p,q)
    need(c[8]==(0x7b,0x4a,-0x958,0),'incoming C1 fee tag')
    for p in(0xa58,0x19d0,0x4ff8,0x5240):need(c[p]==(0x79,0xa1,-0x958,0),'C1 retained fee tag')
    for p in(0xa68,0x1d68):need(c[p]==(0xb7,8,0,1),'C1 Some/None common routing')
    need(c[0x1dd8]==(0xb7,8,0,0)and c[0x12f8]==(0x55,8,1,0),'retained Option discriminator after shared fork')
    def reads_before_overwrite(rr,slot,stop):
        return[p for p,v in rr.items()if p<stop and v[0]==0x79 and v[1]>>4==10 and v[2]==slot]
    observed=[len(reads_before_overwrite(rr,slot,stop))for rr,slot,stop in[(g,-0x928,0x2858),(r,-0x908,0x4b48),(c,-0x958,0x4ff8)]]
    need(observed==[3,2,2],'recomputed fee-validation input reads')
    need(c[0x1d70][0]==r[0x1748][0]==0x71,'preserved fee-edge byte load shape')
    need(c[0x1d98][0]==0x69 and c[0xa70][0]==0x69 and c[0xab0]==(0x79,0xa1,-0x950,0),'C1 common copy/shared gate')
    need(c[0x5390]==(0x79,0xa3,-0x948,0)and c[0x5398]==(0x57,3,0,255)and c[0x53a8][0]==0x55 and c[0x53a8][3]==2,'late raw tag comparison')
    need(c[0x5580]==(0x7b,0x1a,-0x920,0)and c[0x5760]==(0x79,0xa2,-0x920,0),'C1 clone pointer spill/reload')
    need(g[0x5100]==(0x7b,0x1a,-0x8d8,0)and g[0x52e0]==(0x79,0xa2,-0x8d8,0),'original clone pointer spill/reload')
    need(c[0x55a0]==g[0x5120]==(0x71,0x16,46,0)and c[0x57c0]==g[0x5340]==(0x73,0x6a,-0x4e8,0),'original-style bump register')
    need(r[0x50c0]==(0x07,6,0,-0x610)and r[0x50f0]==(0x7b,0x1a,-0x8d8,0),'control opposite allocation')
    return{'feeValidationTests':dict(zip(['original','control','C1'],observed)),'C1SomeSharedGate':'common +0xa70 / test +0xac8, no private Some gate','retainedOptionDiscriminator':'r8 tested at +0x12f8 after shared fork','lateRawTag':True,'clonePointer':'C1 spill FP-0x920; original spill FP-0x8d8','bump':'C1/original r6; control spills','limits':'Exact local CFG/raw witnesses, not original Rust source order or semantic equivalence.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path);args=p.parse_args();here=Path(__file__).resolve().parent
    repo=args.repo.resolve()if args.repo else next((q for q in here.parents if(q/'evidence/original/pump/deployed.so').is_file()),None);need(repo is not None,'provide --repo with checked-in original and pinned binary CORE inputs')
    m=js((here/'inputs.json').read_bytes());need(m['historicalControl']==CONTROL and m['historicalCandidate']==CANDIDATE,'manifest source cohort');archive=(here/m['archive']['path']).read_bytes();need(sha(archive)==m['archive']['sha256']and len(archive)==m['archive']['bytes'],'sealed archive')
    packed=tarbytes(archive);need(set(packed)==set(m['archive']['members']),'outer archive domain');data={n:b for n,(b,e)in packed.items()}
    for n,b in data.items():need(m['archive']['members'][n]=={'bytes':len(b),'sha256':sha(b)},'outer member '+n)
    original=(repo/'evidence/original/pump/deployed.so').read_bytes();need(sha(original)==ORIGINAL,'checked-in original image')
    order=js((here/'original-order.json').read_bytes());os,_=elf(original);h,t=os['.text'];base=141840-h[3];oo=t[base:base+27400]
    need(order['originalSha256']==ORIGINAL,'original order source binding')
    for x in order['witnesses']:
        pos=int(x['relative'],16);need(oo[pos:pos+len(bytes.fromhex(x['raw']))].hex()==x['raw'],'original ordering raw witness')
    z={};prov={}
    for k,commit in [('control',CONTROL),('c1',CANDIDATE)]:
        raw=data['raw/'+k+'.zip'];need(m['rawArchives'][k]=={'member':'raw/'+k+'.zip','sha256':sha(raw),'members':43 if k=='control'else 45},'raw archive declarations');need(sha(raw)==ZIP_SHA[k],'raw ZIP identity');z[k]=zipfile.ZipFile(io.BytesIO(raw));need(len(z[k].namelist())==(43 if k=='control'else 45),'raw ZIP census');prov[k]=provenance(z[k],commit,data,repo)
        need(sha(z[k].read('unstripped.so'))==ELF_SHA[k],'unstripped identity')
    need(prov['control'][1]['files']==prov['c1'][1]['files'],'same236 CORE')
    cp={n.removeprefix('core-source/')for n in data if n.startswith('core-source/')};allcore={x['path']for x in prov['c1'][1]['files']}
    need(cp==set(m['coreArchivedPaths'])and allcore-cp==set(m['coreExternalBinaryPaths']),'CORE storage declarations')
    ref=js(z['c1'].read('reference-admission.json'));need(ref['base']==CONTROL and ref['run']==41159607118 and ref['artifactId']==13026402898 and ref['originalZipSha256']==ZIP_SHA['control'] and ref['coreEqual'],'C1 reference identity')
    need(set(ref['files'])==set(z['control'].namelist()),'C1 reference43 domain')
    for n,e in ref['files'].items():
        b=z['control'].read(n);need(len(b)==e['bytes']and sha(b)==e['sha256'],'C1 referenced control member '+n)
    changed=lambda x,y:[n for n in x if x[n]!=y[n]]
    need(set(prov['control'][2])==set(prov['c1'][2])and changed(prov['control'][2],prov['c1'][2])==[LEAF],'sole staged source delta')
    source={k:prov[k][3][LEAF][0]for k in z};volatile=b'unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};'
    need(all(x.count(volatile)==1 for x in source.values()),'existing fee-edge volatile preserved')
    patch=''.join(difflib.unified_diff(source['control'].decode().splitlines(True),source['c1'].decode().splitlines(True),fromfile='a/'+LEAF,tofile='b/'+LEAF)).encode();need(patch==(here/'source.patch').read_bytes()and m['sourcePatch']=={'path':'source.patch','bytes':len(patch),'sha256':sha(patch)},'exact frozen source patch')
    old,new=(z[k].read('unstripped.so')for k in('control','c1'));score={k:js(z[k].read('score.json'))for k in z};a,b=score['control']['windows'],score['c1']['windows'];need(set(a)==set(b)and len(a)==1035,'saved1035-row domain')
    losses=[n for n in a if a[n]['raw']and not b[n]['raw']];need(len(losses)==687 and all(a[n]['normalized']==b[n]['normalized']for n in a),'saved no-loss arithmetic')
    need((sum(x['normalized']for x in b.values()),sum(x['raw']for x in b.values()))==(1034,347),'saved totals')
    for k in z:
        w=score[k]['windows'];sm=score[k]['summary'];need(sm['candidate_sha256']==ELF_SHA[k]and sm['total']==len(w)and sm['raw']==sum(x['raw']for x in w.values())and sm['normalized']==sum(x['normalized']for x in w.values()),'saved summary recomputation')
    need(sorted(score['c1']['summary']['raw_losses'],key=lambda n:int(n,0))==[hex(n)for n in sorted(map(int,losses))],'saved raw-loss declaration')
    need(set(z['c1'].namelist()).isdisjoint({'RESULT.json'})and 'FAILURE.json'in z['c1'].namelist(),'native failure retained')
    fail=js(z['c1'].read('FAILURE.json'));need(fail['base']==CANDIDATE and fail['type']=='ValueError'and'raw or normalized losses'in fail['message'],'mandatory original failure')
    comparison=js(z['c1'].read('CANDIDATE-COMPARISON.json'));changedrows={n:{'reference':a[n],'candidate':b[n]}for n in a if a[n]!=b[n]};need(comparison['changedRows']==changedrows and len(changedrows)==687 and comparison['noNormalizedLosses']and not comparison['noRawLosses'],'saved rejecting comparison')
    need(prov['c1'][5]['seconds']==87.8,'recorded candidate duration')
    result={'status':'PASS_HISTORICAL_NEGATIVE_PRESERVED','sourcePair':[CONTROL,CANDIDATE],'sourceFiles':141,'stageFiles':142,'COREFiles':236,'nativeBuildSeconds':87.8,'nativeConclusion':'FAIL/no-loss guard','savedScore':{'normalized':1034,'raw':347,'rawLosses':687},'layout':exterior(old,new),'rawProof':rawproof(old,new,original),'limits':'Verifies archived declarations, recorded score arithmetic and bounded raw/layout facts. No compile, IR run, VM, full scorer, source gain, original-source-order or latest-main executable claim.'}
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
