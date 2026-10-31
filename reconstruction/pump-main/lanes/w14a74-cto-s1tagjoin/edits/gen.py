import itertools,sys
import sys; s=open(sys.argv[1] if len(sys.argv)>1 else "programs/pump/src/creator/admin_cto.rs").read()
line=[l for l in s.split('\n') if 'admin_cto_sharing_config(' in l][0]
a=line.index('AdminCtoSharingConfig{')+len('AdminCtoSharingConfig{'); b=line.index('},signer_seeds),val)')
body=line[a:b]
parts=[];d=0;cur=''
for ch in body:
    if ch in '{(': d+=1
    if ch in '})': d-=1
    if ch==',' and d==0: parts.append(cur);cur=''
    else: cur+=ch
parts.append(cur)
names=[p.split(':',1)[0] for p in parts]
TAI={'pool_authority':'a.pool_authority.to_account_info()','authority':'a.admin_set_creator_authority.to_account_info()','global':'a.global.to_account_info()','mint':'a.mint.to_account_info()','sharing_config':'a.sharing_config.to_account_info()','event_authority':'a.pump_fees_event_authority.to_account_info()','program':'a.pump_fees.to_account_info()'}
lit=[n for n,p in zip(names,parts) if p.split(':',1)[1]!=TAI[n]]
print(names,lit,file=sys.stderr)
def mk(sel,tag):
    nb=','.join((n+':'+TAI[n]) if n in sel else p for n,p in zip(names,parts))
    open(tag+'.py','w').write('EDITS=[(%r,%r)]\n'%(body,nb))
for n in lit: mk({n},'r1_'+n)
short={'pool_authority':'pa','authority':'au','global':'gl','mint':'mi','event_authority':'ev','program':'pr'}
names_lit=lit
todo=[]
for k in range(2,len(lit)):
    for c in itertools.combinations(lit,k):
        tag='lat_'+'_'.join(short[x] for x in c); mk(set(c),tag); todo.append(tag)
print(' '.join(todo))
mk(set(lit),'s1')
