#!/usr/bin/env python3
"""var.py <admin_cto.rs> <spec.json>: rewrite CPI account initializers.
spec: {"tcf":{field:form}, "sh":{field:form}}; form = "tai" | order letters KLDOR SWE (e.g. "KLDORSWE") | "raw:<text>"."""
import sys,json,re
F={'K':'key:x.key','L':'lamports:x.lamports.clone()','D':'data:x.data.clone()','O':'owner:x.owner','R':'rent_epoch:x.rent_epoch','S':'is_signer:x.is_signer','W':'is_writable:x.is_writable','E':'executable:x.executable'}
ACC={'tcf':{'system_program':'a.system_program','quote_mint':'a.quote_mint','token_program':'a.quote_token_program','payer':'a.admin_set_creator_authority','associated_token_program':'a.associated_token_program','coin_creator':'a.current_creator','coin_creator_vault_authority':'a.coin_creator_vault_authority','coin_creator_vault_ata':'a.coin_creator_vault_ata','pump_creator_vault':'a.creator_vault','pump_creator_vault_ata':'a.creator_vault_quote_token_account','event_authority':'a.pump_amm_event_authority','program':'a.pump_amm'},
     'sh':{'pool_authority':'a.pool_authority','authority':'a.admin_set_creator_authority','global':'a.global','mint':'a.mint','sharing_config':'a.sharing_config','event_authority':'a.pump_fees_event_authority','program':'a.pump_fees'}}
DOUBLE={'a.quote_mint','a.global','a.bonding_curve'}
KEYS={'tcf':'TransferCreatorFeesToPumpV2{','sh':'AdminCtoSharingConfig{'}
def fields(L,key):
    j=L.index(key)+len(key)-1; d=0; st=j+1; out=[]; i=j+1
    while True:
        ch=L[i]
        if ch in '{([': d+=1
        elif ch in '})]':
            if d==0: out.append((st,i)); return out,i
            d-=1
        elif ch==',' and d==0: out.append((st,i)); st=i+1
        i+=1
def prefix(acc,old):
    m=re.match(r'\{(let x[^;]*;)',old)
    if m: return m.group(1)
    return 'let x:&AccountInfo=%s.as_ref()%s;'%(acc,'.as_ref()' if acc in DOUBLE else '')
def form(acc,old,f):
    if f=='tai': return acc+'.to_account_info()'
    if f.startswith('raw:'): return f[4:]
    pre=f.split('|')[1] if '|' in f else prefix(acc,old)
    o=f.split('|')[0]
    assert sorted(o)==sorted('KLDORSWE'),o
    return '{'+pre+'AccountInfo{'+','.join(F[c] for c in o)+'}}'
def apply(src,spec):
    lines=src.split('\n')
    for grp,mp in spec.items():
        if grp in ('order','rep'): continue
        k=KEYS[grp]; ln=next(i for i,l in enumerate(lines) if k in l); L=lines[ln]
        fs,end=fields(L,k); body=L[fs[0][0]:end]
        parts={}; order=[]
        for a,b in fs:
            t=L[a:b]; n,v=t.split(':',1); parts[n]=v; order.append(n)
        for n,f in mp.items():
            parts[n]=form(ACC[grp][n],parts[n],f)
        if spec.get('order',{}).get(grp): order=spec['order'][grp]
        lines[ln]=L[:fs[0][0]]+','.join(n+':'+parts[n] for n in order)+L[end:]
    out='\n'.join(lines)
    for a,b in spec.get('rep',[]):
        assert out.count(a)==1,(out.count(a),a); out=out.replace(a,b)
    return out
if __name__=='__main__':
    p=sys.argv[1]; spec=json.loads(open(sys.argv[2]).read()) if not sys.argv[2].startswith('{') else json.loads(sys.argv[2])
    s=open(p).read(); t=apply(s,spec); assert t.count('\n')==s.count('\n'); open(p,'w').write(t)
