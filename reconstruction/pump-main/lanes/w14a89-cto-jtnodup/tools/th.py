"""th.py: generic three-hop IR edits (experiment only). th.val(t): validate arms write into the sret; th.ex(t,mode): execute ?-chain collapse."""
import re
VF='define internal void @_ZN14pump_recovered9admin_cto8validate17h'
EF='define hidden { i64, ptr } @_ZN14pump_recovered9admin_cto7execute17h'
def fn(t,F):
    k=t.index(F); e=t.index('\n}\n',k); return k,e
def blocks(b): return b.split('\n\n')
def val(t):
    k,e=fn(t,VF); b=t[k:e]
    b,n=re.subn(r'  call void @llvm.lifetime.(start|end).p0\(i64 32, ptr %target\)\n','',b); assert n>=2,n
    for src in ('%t','%holder_key'):
        x=f'call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target, ptr align 1 {src}, i64 32, i1 false)'
        assert b.count(x)==1,(src,b.count(x)); tag='w'+src[1:3]
        b=b.replace(x,f'%{tag} = getelementptr inbounds i8, ptr %_0, i64 1\n  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %{tag}, ptr align 1 {src}, i64 32, i1 false)')
    m=re.search(r'  call void @llvm.lifetime.start.p0\(i64 32, ptr (%_\d+)\)\n  call void @llvm.memcpy.p0.p0.i64\(ptr align 1 \1, ptr align 1 %target, i64 32, i1 false\)\n  (%\d+) = getelementptr inbounds i8, ptr %_0, i64 1\n  call void @llvm.memcpy.p0.p0.i64\(ptr align 1 \2, ptr align 1 \1, i64 32, i1 false\)\n  store i8 0, ptr %_0, align 8\n  call void @llvm.lifetime.end.p0\(i64 32, ptr \1\)\n',b)
    assert m; b=b[:m.start()]+'  store i8 0, ptr %_0, align 8\n'+b[m.end():]
    assert '%target' not in b.replace('%target = alloca','')
    return t[:k]+b+t[e:]
def ex(t,mode='arms'):
    pin=(mode=='pin')
    k,e=fn(t,EF); b=t[k:e]; B=blocks(b)
    ji=[i for i,x in enumerate(B) if re.search(r'memcpy.p0.p0.i64\(ptr align 1 %target, ptr align 1 %val, i64 32',x)]; assert len(ji)==1,ji; ji=ji[0]
    J=B[ji].split('\n'); hdr=J[0]
    s=[i for i,l in enumerate(J) if re.search(r'getelementptr inbounds i8, ptr %_\d+, i64 1$',l)][0]
    ret=re.search(r'ptr (%_\d+), i64 1$',J[s]).group(1)
    end=[i for i,l in enumerate(J) if re.search(r'lifetime.end.p0\(i64 40, ptr %_\d+\)$',l) and i>s]
    end=[i for i in end if any('%val' in J[j] for j in range(s,i))][0]
    LT=[l for l in J[end+1:] if 'lifetime.start' in l]
    rest=[l for l in J[end+1:] if 'lifetime.start' not in l]
    term=J[-1]; m=re.match(r'\s*br i1 (%\S+), label %(\S+), label %(\S+)',term); sh,A,Bn=m.groups()
    J=J[:s]+(LT if mode=='keeplt' else [])+rest; B[ji]='\n'.join(J)
    def find(name): return [i for i,x in enumerate(B) if x.split('\n')[0].startswith(name+':')][0]
    ai=find(A); last=B[ai].split('\n')[-1]; am=re.match(r'\s*br i1 (%\S+), label %(\S+), label %(\S+)',last)
    if am: H,N=am.group(2),am.group(3)
    else:
        sw=B[ai]; H=re.search(r'i64 0, label %(\S+)',sw).group(1); N=re.search(r'i64 1, label %(\S+)',sw).group(1)
    def cp(tag): return [f'  %x{tag} = getelementptr inbounds i8, ptr {ret}, i64 1',f'  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %target, ptr align 1 %x{tag}, i64 32, i1 false)']
    def ins(name,lines):
        i=find(name); L=B[i].split('\n'); B[i]='\n'.join([L[0]]+lines+L[1:])
    if mode!='keeplt': ins(A,LT); ins(Bn,LT)
    ins(H,cp('a')); ins(Bn,cp('b'))
    if mode=='all3': ins(N,cp('c'))
    if mode=='pin':
        ins(Bn,[f'  %pin{i} = load volatile i8, ptr %new, align 1' for i in range(8)])
    for key,nm in (('A',A),('Bn',Bn),('H',H),('N',N)):
        if EXTRA.get(key): ins(nm,[l.replace('@RET@',ret) for l in EXTRA[key]])
    if EXTRA.get('names') is not None: EXTRA['names'].update(A=A,Bn=Bn,H=H,N=N,J=hdr)
    b='\n\n'.join(B); return t[:k]+b+t[e:]
EXTRA={}
