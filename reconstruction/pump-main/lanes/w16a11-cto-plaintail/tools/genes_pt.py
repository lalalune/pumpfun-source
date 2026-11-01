# w16a11 plaintail genes (experiment only): faithful tail forms as unions, on main 1f4e396 (sweeptuple #3859).
# Each gene is a list of exact single-occurrence (old,new) replacements or callables; the line count must hold.
import os,sys,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_lac as _S
G=_S.G
def apply(s,names): return _S.apply(s,names)

_LIT=re.compile(r'\{let x:&AccountInfo=\s*([^;]+);AccountInfo\{[^}]*\}\}')
def _lits(s):
    out=[]
    for m in _LIT.finditer(s):
        out.append((m.start(),m.end(),m.group(1).strip()))
    return out
# account expression -> plain to_account_info() spelling
def _tai(expr):
    e=expr
    for suf in ('.as_ref().as_ref()','.as_ref()'):
        if e.endswith(suf): e=e[:-len(suf)]; break
    return e+'.to_account_info()'
def _repl(sel):
    """replace the {let x:&AccountInfo=E;AccountInfo{..}} literals whose (context-name) is selected by sel(name,expr)"""
    def g(s):
        res=[];last=0;n=0
        for a,b,e in _lits(s):
            ctx=s[max(0,a-40):a]
            m=re.search(r'([A-Za-z_]+):$',ctx); name=m.group(1) if m else ('CPIPROG' if ctx.endswith('CpiContext::new(') else '?')
            if sel(name,e):
                res.append(s[last:a]); res.append(_tai(e)); last=b; n+=1
        res.append(s[last:]); t=''.join(res)
        assert n>0,'no literal selected'
        return t
    return g
_TCF_ATA={'coin_creator_vault_ata','pump_creator_vault_ata'}
_SH={'pool_authority','authority','global','mint','program_fees'}
# sharing CPI literals: the ones whose expr is a sharing account
_SHEXPR={'a.pool_authority.as_ref()','a.admin_set_creator_authority.as_ref()','a.global.as_ref().as_ref()','a.mint.as_ref()','a.pump_fees.as_ref()'}
_EVLIT=("event_authority:AccountInfo{data:a.pump_fees_event_authority.data.clone(),lamports:a.pump_fees_event_authority.lamports.clone(),key:a.pump_fees_event_authority.key,owner:a.pump_fees_event_authority.owner,rent_epoch:a.pump_fees_event_authority.rent_epoch,is_signer:a.pump_fees_event_authority.is_signer,is_writable:a.pump_fees_event_authority.is_writable,executable:a.pump_fees_event_authority.executable}",
        "event_authority:a.pump_fees_event_authority.to_account_info()")
# S: s1, all seven sharing AccountInfos as plain to_account_info()
G['pS']=[_repl(lambda n,e: e in _SHEXPR),_EVLIT]
# T: tai, the TCF program (CpiContext program + program: field) as a.pump_amm.to_account_info()
G['pT']=[_repl(lambda n,e: e=='a.pump_amm.as_ref()')]
# C: c2 family, the TCF ATAs as to_account_info() (derive clone order = lamports right after key)
G['pC']=[_repl(lambda n,e: n in _TCF_ATA)]
# N: n1po (no nf local + owner-first pool gate)
G['pN']=list(G['n1'])+list(G['po'])
G['pn1']=list(G['n1']); G['ppo']=list(G['po'])
# R: raw-first in the sweep token arm (w14a50 rev_ff)
G['pR']=[("let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;",
          "let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;")]
# P: pool CPI args inline, no pargs tuple (w15a04 p2 without n1)
G['pP']=[("let pargs=(target,a.bonding_curve.is_holder_reward,fee);",""),
         ("signer_seeds),pargs.0,pargs.1,pargs.2)?;","signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;")]
# L_vol head (w15a32 section 8): mv_5_1+t1n+m_crl2+vol334_back
G['Lv']=list(G['mv_5_1'])+list(G['t1n'])+list(G['m_crl2'])+list(G['vol334_back'])
