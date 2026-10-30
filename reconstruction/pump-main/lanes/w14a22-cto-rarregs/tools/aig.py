# aig.py: AccountInfo form genes on the given base source: L<i> to_account_info -> literal, T<j> literal -> to_account_info
import re,json,sys
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a22-cto-rarregs/tools'); import fg
s=fg.apply(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a22-cto-rarregs/var/m3/src/creator/admin_cto.rs').read(),sys.argv[1].split(','))
LIT='{{let x:&AccountInfo={e};AccountInfo{{key:x.key,owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}}}'
def uniq(st,en,new):
    for c in range(0,300,4):
        a=s[max(0,st-c):en]; 
        if s.count(a)==1: return (a, s[max(0,st-c):st]+new)
G={}
for i,m in enumerate(re.finditer(r'([a-z_]+):a\.([a-z_]+)\.to_account_info\(\)',s)):
    p=uniq(m.start(),m.end(),f'{m.group(1)}:'+LIT.format(e=f'a.{m.group(2)}.as_ref()'))
    if p: G[f'AL{i}_{m.group(1)}_{m.group(2)}']=[p]
for j,m in enumerate(re.finditer(r'([a-z_]+):\{let x(?::&AccountInfo)?= ?(&\*)?a\.([a-z_]+)(\.as_ref\(\))*;AccountInfo\{[^}]*\}\}',s)):
    p=uniq(m.start(),m.end(),f'{m.group(1)}:a.{m.group(3)}.to_account_info()')
    if p: G[f'AT{j}_{m.group(1)}_{m.group(3)}']=[p]
json.dump(G,open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a22-cto-rarregs/aig.json','w'))
print(len(G)); print('\n'.join(G))
