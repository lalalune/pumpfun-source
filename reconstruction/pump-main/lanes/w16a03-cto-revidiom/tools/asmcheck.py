import sys,os,collections
sys.path.insert(0,os.path.dirname(__file__))
import shape,srcmap
tot=0; same=0; bad=[]
for w in shape.windows():
    f=srcmap.fn_for(w)
    if not f: continue
    ins=srcmap.win_insns(w); body=srcmap._funcs[f]
    a=[t.split()[0] for _,t,_ in ins]; b=[s.split()[0] for s,l in body]
    tot+=1
    if a==b: same+=1
    else:
        # first mismatch
        k=next((i for i in range(min(len(a),len(b))) if a[i]!=b[i]),min(len(a),len(b)))
        bad.append((w[0],len(a),len(b),k,ins[k][1] if k<len(ins) else '',body[k][0] if k<len(body) else ''))
print('windows with asm fn',tot,'mnemonic-identical',same)
for x in bad[:25]: print(hex(x[0]),x[1:],)
