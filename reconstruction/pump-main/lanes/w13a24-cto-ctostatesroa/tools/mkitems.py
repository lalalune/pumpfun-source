import re,sys
t=open(sys.argv[1]).read()
m=re.search(r'define [^\n]*admin_cto7execute[^\n]*\n',t); s=t[m.end():]; s=s[:s.index('\n}\n')]
al=re.findall(r'^  %([\w.$"]+) = alloca',s,re.M)
lt=set(re.findall(r'lifetime\.start\.p0\(i64 \d+, ptr nonnull %([\w.$]+)\)',s))
k=max(i for i,a in enumerate(al) if a.endswith('.i') or re.search(r'\.i\d+$',a))
ex=al[k+1:]; top=al[0]
items=['nolt:'+a for a in al if a in lt]
for x in ex: items+= [f'mv:{x}:{top}', f'mv:{x}:END']
extra=sys.argv[3:] 
for x in extra:
    for b in ex:
        if b!=x: items.append(f'mv:{x}:{b}')
open(sys.argv[2],'w').write('\n'.join(items)+'\n'); print(len(items), 'exec allocas', len(ex))
