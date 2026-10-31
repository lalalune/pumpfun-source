#!/usr/bin/env python3
"""lab2src.py <out.py> <base_edits.py> <log.jsonl>...: accepted pscan labs per clone -> source T() on the TCF CPI segment.
Clone literal fields keep their existing expressions (e.g. data:a.pump_amm.data.clone()); only the order changes."""
import re
ORDER=['key','owner','rent','f40','f41','f42']; NM={'key':'key','owner':'owner','rent':'rent_epoch','f40':'is_signer','f41':'is_writable','f42':'executable'}
# clone -> (segment marker, field prefix, accessor)   'TCF' = TransferCreatorFeesToPumpV2 line
C={'%x.i':('TCF','CpiContext::new(','a.pump_amm.as_ref()'),
 '%_227.i':('TCF','payer:','a.admin_set_creator_authority.as_ref()'),
 '%_228.i':('TCF','quote_mint:','a.quote_mint.as_ref().as_ref()'),
 '%_229.i':('TCF','token_program:','a.quote_token_program.as_ref()'),
 '%_230.i':('TCF','system_program:','a.system_program.as_ref()'),
 '%_231.i131':('TCF','associated_token_program:','a.associated_token_program.as_ref()'),
 '%_232.i132':('TCF','coin_creator_vault_authority:','a.coin_creator_vault_authority.as_ref()'),
 '%x11.i':('TCF','coin_creator_vault_ata:','a.coin_creator_vault_ata.as_ref()'),
 '%x12.i':('TCF','pump_creator_vault_ata:','a.creator_vault_quote_token_account.as_ref()'),
 '%_249.i136':('TCF','event_authority:','a.pump_amm_event_authority.as_ref()'),
 '%x13.i':('TCF','program:','a.pump_amm.as_ref()')}
def span(seg,pre):
    i=[m.start() for m in re.finditer(r'(?<=[{,(])'+re.escape(pre),seg)]
    assert len(i)==1,(pre,len(i)); s=i[0]+len(pre)
    if seg[s]=='{':
        d=0
        for k in range(s,len(seg)):
            d+= {'{':1,'}':-1}.get(seg[k],0)
            if d==0: return s,k+1
    m=re.match(r'[\w.]+\.to_account_info\(\)',seg[s:]); return s,s+m.end()
def fields(expr):
    m=re.search(r'AccountInfo\{(.*)\}\}$',expr)
    if not m: return {}
    out={}
    for p in re.split(r',(?=[a-z_]+:)',m.group(1)):
        k,v=p.split(':',1); out[k]=v
    return out
def newlit(acc,lab,old):
    rc=lab.endswith(':rc'); lab=lab[:-3] if rc else lab
    a,o=lab.split(':'); asg=dict(zip(ORDER,['P'+c for c in a])); o=o.split('.')
    F=fields(old); f=lambda k:k+':'+F.get(k,'x.'+k+('.clone()' if k in('lamports','data') else ''))
    g=lambda P:[f(NM[n]) for n in o if asg[n]==P]
    r1,r2=(f('data'),f('lamports')) if rc else (f('lamports'),f('data'))
    return '{let x:&AccountInfo='+acc+';AccountInfo{'+','.join(g('P0')+[r1]+g('P1')+[r2]+g('P2'))+'}}'
C1={'%x11.i':('TCF','payer:','a.admin_set_creator_authority.as_ref()'),
 '%_280.i':('TCF','quote_mint:','a.quote_mint.as_ref().as_ref()'),
 '%x12.i':('TCF','token_program:','a.quote_token_program.as_ref()'),
 '%_289.i':('TCF','system_program:','a.system_program.as_ref()'),
 '%x13.i':('TCF','associated_token_program:','a.associated_token_program.as_ref()'),
 '%x14.i':('TCF','coin_creator_vault_authority:','a.coin_creator_vault_authority.as_ref()'),
 '%x15.i':('TCF','coin_creator_vault_ata:','a.coin_creator_vault_ata.as_ref()'),
 '%x16.i':('TCF','pump_creator_vault_ata:','a.creator_vault_quote_token_account.as_ref()'),
 '%x17.i':('TCF','event_authority:','a.pump_amm_event_authority.as_ref()'),
 '%x18.i':('TCF','program:','a.pump_amm.as_ref()'),
 '%_427':('SH','CpiContext::new_with_signer(','a.pump_fees.as_ref()'),
 '%x':('SH','pool_authority:','a.pool_authority.as_ref()'),
 '%x18':('SH','authority:','a.admin_set_creator_authority.as_ref()'),
 '%x19':('SH','global:','a.global.as_ref().as_ref()'),
 '%x20':('SH','mint:','a.mint.as_ref()'),
 '%_461':('SH','sharing_config:','a.sharing_config.as_ref()'),
 '%x21':('SH','program:','a.pump_fees.as_ref()')}
C2={'%x.i':('TCF','CpiContext::new(','a.pump_amm.as_ref()'),
 '%x11.i':C1['%x11.i'],'%_280.i':C1['%_280.i'],'%x12.i':C1['%x12.i'],'%_289.i':C1['%_289.i'],'%x13.i':C1['%x13.i'],'%x14.i':C1['%x14.i'],
 '%x15.i':C1['%x15.i'],'%x16.i':C1['%x16.i'],'%x17.i':C1['%x17.i'],'%x18.i':C1['%x18.i'],
 '%x':C1['%_427'],'%x18':C1['%x'],'%x19':C1['%x18'],'%x20':C1['%x19'],'%x21':C1['%x20'],'%_477':C1['%_461'],'%x22':C1['%x21']}
MK={'TCF':'TransferCreatorFeesToPumpV2{payer:','SH':'AdminCtoSharingConfig{'}
def apply(s,acc):
    for key,lab in acc:
        sg,pre,ac=key
        i=s.index(MK[sg]); i=s.rindex('\n',0,i); j=s.index('\n',i+1); seg=s[i:j]
        a,b=span(seg,pre); seg=seg[:a]+newlit(ac,lab,seg[a:b])+seg[b:]; s=s[:i]+seg+s[j:]
    return s
if __name__=='__main__':
    import sys,json
    out,base=sys.argv[1:3]; acc={}
    for lf in sys.argv[3:]:
        CC=C if lf.startswith('cd1') else C2 if lf.startswith('cd3') else C1
        for l in open(lf):
            r=json.loads(l)
            if r.get('accepted'): acc[CC[r['clone']]]=r['best']['lab']
    acc=list(acc.items())
    open(out,'w').write(open(base).read()+'\nimport sys\nsys.path.insert(0,%r)\nfrom lab2src import apply as _ap\nACC=%r\ndef T(s): return _ap(s,ACC)\n'%(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),acc))
    print(acc)
