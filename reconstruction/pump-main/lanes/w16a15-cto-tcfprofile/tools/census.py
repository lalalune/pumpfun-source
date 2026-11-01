#!/usr/bin/env python3
"""census.py <sbs.txt> : per-clone census of the TCF clone run between successive abort jumps (orig ja 26e0)."""
import sys,re,json
CL=['ctx program (a1 manual, pump_amm)','payer (admin_set_creator_authority)','quote_mint','token_program (quote_token_program)',
    'system_program','associated_token_program','coin_creator (current_creator)','coin_creator_vault_authority',
    'coin_creator_vault_ata (a2 manual)','pump_creator_vault (creator_vault)','pump_creator_vault_ata (a3 manual, pcva)',
    'event_authority (pump_amm_event_authority)','program (a4 manual, pump_amm)']
L=[l.rstrip('\n') for l in open(sys.argv[1])]
# segment boundaries: orig abort block 026e0 call, then each '= .... ja r0, 26e0'
start=next(i for i,l in enumerate(L) if l.startswith('= 026e0'))
segs=[];cur=[];k=start+1
for l in L[start+1:]:
    if l.startswith('= ') and 'ja r0, 26e0' in l.split('|')[0]:
        segs.append(cur); cur=[]
        if len(segs)==25: break
        continue
    cur.append(l)
rows=[]
for i,s in enumerate(segs):
    c=0 if i==0 else (i+1)//2
    part='dat' if i==0 else ('lam' if i%2==1 else 'dat')
    plus=[l.split('|')[1].strip() for l in s if l.startswith('+')]
    minus=[l.split('|')[0][2:].strip() for l in s if l.startswith('-')]
    no=sum(1 for l in s if not l.startswith('+')); nm=sum(1 for l in s if not l.startswith('-'))
    rows.append({'seg':i,'clone':c+1,'field':CL[c],'part':part,'orig_ins':no,'main_ins':nm,'delta_B':8*(nm-no),'main_extra':plus,'orig_extra':minus})
json.dump(rows,open(sys.argv[2],'w'),indent=1) if len(sys.argv)>2 else None
for r in rows:
    print(f"seg{r['seg']:2d} clone{r['clone']:2d} {r['part']} {r['field'][:34]:34s} orig {r['orig_ins']:2d} main {r['main_ins']:2d} d {r['delta_B']:+4d} | main+ {r['main_extra']} | orig+ {r['orig_extra']}")
