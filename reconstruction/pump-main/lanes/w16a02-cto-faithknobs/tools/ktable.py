#!/usr/bin/env python3
"""ktable.py: markdown rows for the sibling-idiom knobs built on main 1f4e396 (res-1f4e396.jsonl), with where their
bytes land relative to the new main and whether they equal it. Bookkeeping for NOTES.md."""
import json,os,sys
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import region, genes_fk
from oracle import mask
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a02-cto-faithknobs')
NEW=open(O+'/rx/H_ev6_A6/fn.bin','rb').read()
SIB={'k_rkn307':'create_v2 `require_keys_neq!`','k_req312':'`require!`','k_req326':'admin_cto_pool `require!(!..)`','k_req330':'admin_cto_pool `require!(!..)`',
     'k_req334':'create_v2 `require!`','k_req338':'admin_cto_pool `require!(a>0&&a<=max)`','k_iflet326':'admin_cto_pool `if let Some(..)`',
     'k_okor306':'distribute_creator_fee_v2 `ok_or_else`','k_cbif':'admin_cto_pool `if holder{false}else{..}`','k_rentdirect':'sweep_fees `Rent::get()?.minimum_balance(0)`',
     'k_oldfee_after':'admin_cto_pool old fee read after the stores','k_amutstar':'sweep_fees `&mut *ctx.accounts`','k_wl_early':'collect_creator_fee early-return `msg!`',
     'k_wl_early2':'collect_creator_fee early-return `msg!`','k_inl_wallet':'collect_creator_fee `#[inline]` helper','k_inl_sweep':'`#[inline]` helper',
     'k_inl_validate':'`#[inline]` helper','k_dpid':'`crate::id()`'}
for l in [x for f in ('/res-1f4e396.jsonl','/res-5998913.jsonl') if os.path.exists(O+f) for x in open(O+f)]:
    r=json.loads(l); n=r['name']
    if not n.startswith('k_'): continue
    if 'error' in r: print(f"| {n} | {SIB.get(n,'')} | compile error | | |"); continue
    fb=f'{O}/rx/{n}/fn.bin'; x=open(fb,'rb').read()
    note='byte-identical to main' if mask(x)==mask(NEW) else str(region.regions(fb,O+'/rx/H_ev6_A6/fn.bin').get('by_region'))
    g=r.get('genes','')
    print(f"| {n} (on 1f4e396) | {SIB.get(n,'')} | {r['bytes']:,} | {r['M']:,} | {note} |")
