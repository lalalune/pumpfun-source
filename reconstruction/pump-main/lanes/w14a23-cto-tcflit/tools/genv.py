#!/usr/bin/env python3
"""genv.py <outdir> <listfile>: variants of the vault ATA (pump_creator_vault_ata) literal order. name = va_<order>"""
import sys,os
FLD={'K':'key:x.key','L':'lamports:x.lamports.clone()','D':'data:x.data.clone()','O':'owner:x.owner','R':'rent_epoch:x.rent_epoch',
 'S':'is_signer:x.is_signer','W':'is_writable:x.is_writable','E':'executable:x.executable'}
CUR='KRLSDOWE'
def lit(o): return 'pump_creator_vault_ata:{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();AccountInfo{'+','.join(FLD[c] for c in o)+'}}'
d=sys.argv[1]; os.makedirs(d,exist_ok=True)
for l in open(sys.argv[2]):
    n=l.strip()
    if not n: continue
    o=n.split('_')[1]
    open(f'{d}/{n}.py','w').write('EDITS='+repr([(lit(CUR),lit(o))])+'\n')
