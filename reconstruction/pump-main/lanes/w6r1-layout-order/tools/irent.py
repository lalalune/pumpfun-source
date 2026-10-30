import re,sys
exec(open(__file__.rsplit('/',1)[0]+'/irfn.py').read().split('a=fn')[0])
def entry(path,pat):
    b=fn(path,pat)
    if not b: return None
    i=next(k for k,l in enumerate(b) if l.startswith('start:'))
    ent=[]
    for l in b[i+1:]:
        if l.strip()=='' or re.match(r'^\S',l): break
        ent.append(l)
    return [re.sub(r', !noalias !\d+','',l.strip()) for l in ent if 'lifetime.start' in l]
for path,pat in zip(sys.argv[1::2],sys.argv[2::2]):
    e=entry(path,pat); print(pat,len(e) if e is not None else None)
    for l in e or []: print('   ',l[:140])
