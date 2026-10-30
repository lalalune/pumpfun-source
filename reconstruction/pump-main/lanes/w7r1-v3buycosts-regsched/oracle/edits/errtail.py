import re,os
MODE=os.environ.get('ET','ret')
def blocks(f):
    head,body=f.split('\n',1); body=body.rsplit('}',1)[0]
    return head,re.split(r'\n\n',body.strip('\n'))
def edit(f):
    head,bl=blocks(f)
    inc0=[];inc1=[];names=[]
    out=[]
    for b in bl:
        L=b.split('\n')
        nm=re.match(r'("[^"]+"|[\w.$]+):',L[0]).group(1) if not L[0].startswith('start') else 'start'
        if L[-1].strip()=='br label %bb15' and nm!='bb35':
            # find stores to _0+8 and +16
            g8=g16=None
            for l in L:
                m=re.match(r'\s*(%\S+) = getelementptr inbounds i8, ptr %_0, i64 (8|16)$',l)
                if m:
                    if m.group(2)=='8': g8=m.group(1)
                    else: g16=m.group(1)
            v0=v1=None; keep=[]
            for l in L:
                if g8 and re.match(r'\s*store i64 (\S+), ptr '+re.escape(g8)+r',',l): v0=re.match(r'\s*store i64 (\S+),',l).group(1); continue
                if g16 and re.match(r'\s*store ptr (\S+), ptr '+re.escape(g16)+r',',l): v1=re.match(r'\s*store ptr (\S+),',l).group(1); continue
                if re.match(r'\s*(%\S+) = getelementptr inbounds i8, ptr %_0, i64 (8|16)$',l): continue
                keep.append(l)
            assert v0 and v1,(nm,b[:200])
            keep[-1]='  br label %errtail'
            inc0.append('[ %s, %%%s ]'%(v0,nm)); inc1.append('[ %s, %%%s ]'%(v1,nm)); names.append(nm)
            out.append('\n'.join(keep)); continue
        out.append(b)
    et=['errtail:','  %et0 = phi i64 '+', '.join(inc0),'  %et1 = phi ptr '+', '.join(inc1),
        '  %etg8 = getelementptr inbounds i8, ptr %_0, i64 8','  store i64 %et0, ptr %etg8, align 8',
        '  %etg16 = getelementptr inbounds i8, ptr %_0, i64 16','  store ptr %et1, ptr %etg16, align 8']
    if MODE=='ret':
        et+=['  store i64 1, ptr %_0, align 8','  ret void']
        res=[]
        for b in out:
            if b.startswith('bb15:'): continue
            if b.startswith('bb35:'):
                b=b.replace('  br label %bb15','  store i64 0, ptr %_0, align 8\n  ret void')
            res.append(b)
        out=res
    else:
        et+=['  br label %bb15']
        res=[]
        for b in out:
            if b.startswith('bb15:'):
                L=b.split('\n'); L[0]='bb15:'
                L[1]='  %.sink = phi i64 [ 1, %errtail ], [ 0, %bb35 ]'
                b='\n'.join(L)
            res.append(b)
        out=res
    pos=int(os.environ.get('ETPOS','-1'))
    if pos<0: out.append('\n'.join(et))
    else: out.insert(pos,'\n'.join(et))
    return head+'\n'+'\n\n'.join(out)+'\n}\n'
