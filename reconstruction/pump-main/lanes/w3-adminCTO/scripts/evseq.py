# evseq.py orig.ev cand.ev : compare event (call/line) sequences
import sys,re,difflib
def ev(f):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2 or l.startswith('#'): continue
        s=p[1].strip()
        if s.startswith('CALL') or s.startswith('LINE') or s.startswith('SYSCALL') or s.startswith('imm'):
            s=re.sub(r'\s+',' ',s)[:60]; out.append((p[0],s))
    return out
o=ev(sys.argv[1]); c=ev(sys.argv[2])
sm=difflib.SequenceMatcher(None,[x[1] for x in o],[x[1] for x in c],autojunk=False)
print('event ratio',round(sm.ratio(),4),len(o),len(c))
if len(sys.argv)>3:
    for t,i1,i2,j1,j2 in sm.get_opcodes():
        if t!='equal': print(t,[f'{a}:{b[:40]}' for a,b in o[i1:i2]][:6],'|',[f'{a}:{b[:40]}' for a,b in c[j1:j2]][:6])
