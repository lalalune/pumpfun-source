#!/usr/bin/env python3
"""regions.py <unstripped.so> <out.json> : ranked whole-window residual map (splice what-ifs per semantic region)."""
import sys, json, subprocess
from pathlib import Path
T = Path(__file__).resolve().parent
sys.argv_ = sys.argv
so, out = sys.argv[1], sys.argv[2]
sys.argv = ['splice.py']
import importlib.util
spec = importlib.util.spec_from_file_location('splice', T / 'splice.py'); sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)
R = [  # orig lo, hi, label, source lines, owner (running/finished lanes)
 (0x0080, 0x0400, 'entry head: holder-rewards PDA (orig first), shared test (orig creator==key), quote_locked memcmps', '339', 'unowned (w14a09/w14a11 notes: PDA-first = orig head but RA cascade -0.07)'),
 (0x0400, 0x06a8, 'CtoState/holder_key copy + validate head (mayhem, holder tests)', '339,283-296', 'validate (w14a15/w14a21); w14a02/w14a29 notes'),
 (0x06a8, 0x0838, 'validate error blocks 289/298 (Display fmt)', '289,298', 'validate (w14a15/w14a21)'),
 (0x0838, 0x0e08, 'validate 298/312 memcmps, 306/296 error blocks', '296-312', 'validate (w14a15/w14a21)'),
 (0x0e28, 0x1068, 'validate 306/296 error blocks', '296,306', 'validate (w14a15/w14a21)'),
 (0x1068, 0x1940, 'validate fee errors 326/312/307/330/338/334 (to_string outlined in orig)', '307-338', 'validate (w14a15/w14a21); w14a07/w14a10 notes'),
 (0x1940, 0x1c38, 'sharing/collect_old tuple, prepare_bonding_curve, require 410', '339-410', 'w14a29 hcbools notes'),
 (0x1c38, 0x1d30, 'anchor (equal run)', '', 'matched'),
 (0x1d30, 0x2300, 'sweep head: native test, creator-vault PDA, amm_frozen, raw_amount, 660 error', '647-660', 'unowned'),
 (0x2330, 0x2478, 'ConstraintSeeds error block 648', '648', 'unowned'),
 (0x2498, 0x26e8, 'sweep 719 frozen/raw_amount + token_frozen', '719', 'holder vault ATA (w14a27)'),
 (0x26e8, 0x3930, 'TCF transfer_creator_fees_to_pump_v2 inline AccountInfo literals', '661', 'sweep TCF (w14a17/w14a23)'),
 (0x3968, 0x3c38, 'TCF call, Rent::get, native sweep head', '661-663', 'native join (w14a33)'),
 (0x3c38, 0x46b8, 'sharing CPI admin_cto_sharing_config inline literals', '745-751', 'sharing CPI (w14a30)'),
 (0x46b8, 0x4970, 'anchor (equal run, sharing CPI tail)', '749', 'matched'),
 (0x4970, 0x4e60, 'curve update, pool gate, admin_cto_pool clone run + CPI', '752-766', 'curve tail (w14a34); w14a25 notes'),
 (0x4e60, 0x5538, 'AdminCtoEvent build + emit + event CPI', '767', 'unowned (w14a26/w14a20 landed pieces)'),
 (0x5570, 0x5a80, 'tail error blocks: unwrap_failed, mayhem 284, NotWritable 556, Rent min balance', '284,556,663', 'unowned'),
 (0x5a80, 0x5c38, 'sweep native: ensure_rent_exempt + transfer_native + return join', '664', 'native join (w14a33)'),
 (0x5c38, 0x6b08, 'wallet(): flags, ATA create, collect + event, coin CPI', '556-580', 'wallet r8 (w14a35); w14a24 notes'),
]
o, k, on, cn = sp.load(so)
base_r = sp.ratio([t for _, t in o], [t for _, t in k]); base_s = sp.slots(on, cn)
rows = []
for lo, hi, lab, src, own in R:
    nk, ncn = sp.splice(o, k, on, cn, [(lo, hi)])
    r = sp.ratio([t for _, t in o], nk); s = sp.slots(on, ncn)
    rows.append(dict(lo=hex(lo), hi=hex(hi), label=lab, source_lines=src, owner=own, dratio=round(r - base_r, 5), dslots=base_s - s, **sp.split(o, k, lo, hi)))
rank = sorted(rows, key=lambda r: -r['dratio'])
json.dump(dict(main=open(Path.home()/'.cache/pumpfun-reconstruction/w11/current-baseline/MAIN_SHA').read().strip(), base_ratio=round(base_r, 5), base_slots=base_s,
  method='splice orig normalized bytes over [lo,hi) (equal-offset boundaries); dratio/dslots = gain if the region matched exactly; fm/rm/jm/sk = local-alignment misses removed by masking frame / registers / jump offsets, sk = remaining structure misses',
  regions=rows, ranked=[(r['lo'], r['hi'], r['dratio'], r['owner']) for r in rank]), open(out, 'w'), indent=1)
for r in rank: print(r['lo'], r['hi'], r['dratio'], r['dslots'], 'fm', r['fm'], 'rm', r['rm'], 'jm', r['jm'], 'sk', r['sk'], '|', r['owner'][:40])
