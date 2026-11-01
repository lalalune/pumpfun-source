# w16a15 tcfprofile gene library (experiment only). Gene names:
#   <lit>:<order>  permute literal <lit> (lit.py keys a1..a4,b1..b6,...) to the given index order (lit.py tag)
#   P:<spec>       rebuild an AccountInfo literal from a field spec, letters K L D O R S W E (key lamports data owner
#                  rent_epoch is_signer is_writable executable); uppercase reads via `x.`, lowercase via the account path.
#                  Literal chosen by prefix: P=a3 pcva (creator_vault_quote_token_account), Q=a2 cvata, G=a4 program,
#                  H=a1 ctx program.  e.g. P:KLDORSWE (= c2)
#   T<n>:<spec>    replace the n-th TCF to_account_info() field (lit.py 'tcf' field name) with a manual literal per spec
#   named genes in G.
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import lit
G={}
G['c2']=[("pump_creator_vault_ata:{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();AccountInfo{key:x.key,data:a.creator_vault_quote_token_account.data.clone(),owner:a.creator_vault_quote_token_account.owner,lamports:x.lamports.clone(),",
          "pump_creator_vault_ata:{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();AccountInfo{key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,")]
FN={'K':'key','L':'lamports','D':'data','O':'owner','R':'rent_epoch','S':'is_signer','W':'is_writable','E':'executable'}
PATH={'P':'a.creator_vault_quote_token_account','Q':'a.coin_creator_vault_ata','G':'a.pump_amm','H':'a.pump_amm'}
LITK={'P':'a3','Q':'a2','G':'a4','H':'a1'}
def fexpr(c,path):
    f=FN[c.upper()]; base='x' if c.isupper() else path
    return f'{f}:{base}.{f}'+('.clone()' if f in ('lamports','data') else '')
def lit_spec(s,key,path,spec):
    a,b,parts=lit.fields(s,key)
    assert sorted(spec.upper())==sorted('KLDORSWE'),spec
    return s[:a]+','.join(fexpr(c,path) for c in spec)+s[b:]
TCFN=['payer','quote_mint','token_program','system_program','associated_token_program','coin_creator','coin_creator_vault_authority','coin_creator_vault_ata','pump_creator_vault','pump_creator_vault_ata','event_authority','program']
def t_spec(s,field,spec):
    a,b,parts=lit.fields(s,'tcf')
    i=[p.split(':',1)[0] for p in parts].index(field); p=parts[i]
    expr=p.split(':',1)[1]; assert expr.endswith('.to_account_info()'),p
    path=expr[:-len('.to_account_info()')]
    body=','.join(fexpr(c,path) for c in spec)
    new=f'{field}:{{let x:&AccountInfo={path}.as_ref();AccountInfo{{{body}}}}}' if any(c.isupper() for c in spec) else f'{field}:AccountInfo{{{body}}}'
    parts=parts[:i]+[new]+parts[i+1:]
    return s[:a]+','.join(parts)+s[b:]
def apply(s,names):
    for n in names:
        if n in G:
            for e in G[n]:
                a,b=e; c=s.count(a)
                if c!=1: raise Exception(f'gene {n}: {c} occurrences of {a[:100]!r}')
                s=s.replace(a,b)
        elif n[0] in 'PQGH' and n[1]==':':
            s=lit_spec(s,LITK[n[0]],PATH[n[0]],n[2:])
        elif n[0]=='T' and ':' in n:
            k,spec=n[1:].split(':'); s=t_spec(s,TCFN[int(k)],spec)
        elif ':' in n:
            k,tag=n.split(':'); order=[int(c,16) for c in tag]; s=lit.permute(s,k,order)
        else: raise Exception('unknown gene '+n)
    return s
