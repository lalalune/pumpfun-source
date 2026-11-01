#!/usr/bin/env python3
"""lit.py: struct-literal field init-order permutation generator for admin_cto.rs (experiment only).
LITS maps a short key to a unique anchor that ends right before the literal's '{'.
fields(s,key) -> (start,end,[field texts]); permute(s,key,order) -> new source (same line count)."""
import itertools,random
LITS={
 'wcr':'anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.current_creator_quote_token_account',
 'ccf':'crate::pump_amm::cpi::accounts::CollectCoinCreatorFee',
 'tcf':'crate::pump_amm::cpi::accounts::TransferCreatorFeesToPumpV2',
 'scr':'anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.holder_creator_vault_quote_token_account',
 'shc':'crate::pump_fees::cpi::accounts::AdminCtoSharingConfig',
 'pool':'crate::pump_amm::cpi::accounts::AdminCtoPool',
 'ev':'let e=AdminCtoEvent',
 'cev':'let e=CollectCreatorFeeEvent',
 'st':'let st=CtoState',
 'a1':'CpiContext::new({let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo',
 'a2':'coin_creator_vault_ata:{let x:&AccountInfo=a.coin_creator_vault_ata.as_ref();AccountInfo',
 'a3':'pump_creator_vault_ata:{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();AccountInfo',
 'a4':'program:{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo',
 'b1':'pool_authority:{let x:&AccountInfo= a.pool_authority.as_ref();AccountInfo',
 'b2':'authority:{let x:&AccountInfo=a.admin_set_creator_authority.as_ref();AccountInfo',
 'b3':'global:{let x:&AccountInfo= a.global.as_ref().as_ref();AccountInfo',
 'b4':'mint:{let x:&AccountInfo= a.mint.as_ref();AccountInfo',
 'b5':'sharing_config:a.sharing_config.to_account_info(),event_authority:AccountInfo',
 'b6':'program:{let x:&AccountInfo=a.pump_fees.as_ref();AccountInfo',
}
def _anchor(key):
    a=LITS[key]
    return a if a.endswith('Create') is False and not a.endswith('{') else a
def fields(s,key):
    a=LITS[key]; c=s.count(a); assert c==1,(key,c)
    i=s.index(a)+len(a)
    if a.endswith(',associated_token:a.current_creator_quote_token_account') or a.endswith(',associated_token:a.holder_creator_vault_quote_token_account'):
        i=s.index(a)+len('anchor_spl::associated_token::Create')
    assert s[i]=='{',(key,s[i:i+20])
    d=0; j=i; parts=[]; st=i+1
    while True:
        ch=s[j]
        if ch in '([{': d+=1
        elif ch in ')]}':
            d-=1
            if d==0: parts.append(s[st:j]); break
        elif ch==',' and d==1: parts.append(s[st:j]); st=j+1
        j+=1
    assert all('\n' not in p for p in parts),key
    return i+1,j,parts
def names(s,key):
    return [p.split(':',1)[0] if ':' in p else p for p in fields(s,key)[2]]
def permute(s,key,order):
    a,b,parts=fields(s,key); assert sorted(order)==list(range(len(parts)))
    return s[:a]+','.join(parts[k] for k in order)+s[b:]
def moves(n):
    out=[]
    for i in range(n):
        for j in range(n):
            if i==j: continue
            o=list(range(n)); x=o.pop(i); o.insert(j,x)
            if tuple(o) not in out: out.append(tuple(o))
    return out
def tag(order): return ''.join('0123456789abcdefghij'[k] for k in order)
if __name__=='__main__':
    import sys
    s=open(sys.argv[1]).read()
    for k in LITS:
        try: print(k,names(s,k))
        except Exception as e: print(k,'ERR',e)
