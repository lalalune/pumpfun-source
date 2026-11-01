import sys,re,subprocess,os,json,tempfile
sys.path.insert(0,os.path.dirname(__file__)); import oracle
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
base=sys.argv[1]; L=open(base).read().split('\n')
s,e=2722,2752
blk=L[s-1:e]
assert blk[0].strip().startswith('%24 = getelementptr') and blk[-1].strip().startswith('store i8 %26')
MC=[l for l in blk if 'llvm.memcpy' in l][0]
pre=[l for l in blk if not l.strip().startswith('store') and 'llvm.memcpy' not in l and not re.match(r'\s*%(3[7-9]|4[0-4]) = ',l)]
geps=[l for l in blk if re.match(r'\s*%(3[7-9]|4[0-4]) = ',l)]
stores={int(re.search(r'%(\d+), align',l).group(1)):l for l in blk if l.strip().startswith('store')}
# map store ptr -> field offset
off={37:32,38:40,39:41,40:42,41:43,43:44,44:45}
bystoff={off[k]:v for k,v in stores.items()}
def words(vl,vs):
    o=[]
    for k in range(4):
        o+=[f'  %cwp{k} = getelementptr inbounds i8, ptr %27, i64 {8*k}', f'  %cw{k} = load {"volatile " if vl else ""}i64, ptr %cwp{k}, align 8',
            f'  %cwd{k} = getelementptr inbounds i8, ptr %st, i64 {8*k}', f'  store {"volatile " if vs else ""}i64 %cw{k}, ptr %cwd{k}, align 8']
    return o
def st(o,v): 
    l=bystoff[o]; return l.replace('store ','store volatile ',1) if v else l
def build(mc_pos, order, vs, vl=False):
    # mc_pos: 'main' keep memcpy right after %27 gep; 'words' replace by word copies at 'C' in order
    out=[]
    for l in pre:
        out.append(l)
        if mc_pos=='main' and l.strip().startswith('%27 = '): out.append(MC)
    out+=geps
    for k in order:
        if k=='C':
            if mc_pos=='words': out+=words(vl,vs)
            elif mc_pos=='late': out.append(MC)
        else: out.append(st(k,vs))
    return L[:s-1]+out+L[e:]
ORIG=[42,41,40,'C',43,45,44,32]; MAIN=['C',32,40,41,42,43,44,45]
V={'A_main_nv':('main',MAIN,0),'A_main_vs':('main',MAIN,1),'B_orig_vs':('main',ORIG,1),'B_orig_nv':('main',ORIG,0),
   'C_words_vsvl':('words',ORIG,1,1),'D_words_vs':('words',ORIG,1,0),'E_late_vs':('late',ORIG,1),'F_words_main_vsvl':('words',MAIN,1,1)}
orig=oracle.orig_window()
for name,args in V.items():
    T=build(*args); d=tempfile.mkdtemp(prefix='ct',dir='scr'); open(d+'/m.ll','w').write('\n'.join(T))
    r=subprocess.run([SDK+'/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: print(name,'ERR',r.stderr[-300:]); subprocess.run(['rm','-rf',d]); continue
    cb=oracle.elf_fn(d+'/m.o',oracle.KEEP); rr,sd=oracle.metric(cb,orig); open(f'scr/ct_{name}.bin','wb').write(cb)
    print(json.dumps({'name':name,'ratio':round(rr,5),'bytes':len(cb),'slots':sd}),flush=True)
    subprocess.run(['rm','-rf',d])
