#!/usr/bin/env python3
"""tab.py: collect the s3ovarm cell table (raw-IR oracle captures on main 5998913 + e/S3n.py) -> w/table.json"""
import json, os, re
O = '/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a23-cto-s3ovarm'
DESC = {
 'A1': 'ov1a on S3n: validate takes shared:bool; non-holder arm yields if shared{st.creator}else{t}; execute tree keeps its override',
 'A2': 'ov1b on S3n: non-holder arm if !shared{t}else{st.creator}',
 'A3': 'ov1a with hf written per sub-arm (if shared{*hf=false;st.creator}else{*hf=false;t})',
 'A0': 'ov1 on S3n: ov1a and the execute-tree target override removed (target immutable)',
 'A1f': 'A1 + args forwarded (sharing_update=Some(new), no let args=&(new,))',
 'A0f': 'A0 + args forwarded',
 'A1r': 'A1 + event sharing_config_reset:shared (o_rs)',
 'A0r': 'A0 + o_rs',
 'B1': 'su:&mut Option<Option<Pubkey>> out-param written per arm in validate (holder arm Some(None) when shared; shared non-holder arm Some(new) + target st.creator); execute reads su; args dropped',
 'B2': 'B1 with explicit else writes (*su=None) in both arms',
 'B3': 'B1 keeping let args=&(new,) and passing args.0 to validate',
 'B1r': 'B1 + o_rs',
 'B2r': 'B2 + o_rs',
 'B6': 'su written only in the shared non-holder arm (Some(new) + st.creator); holder shared Some(None) stays in execute tree',
 'B6r': 'B6 + o_rs',
 'C1': 'ov2 on S3n: validate returns Result<(Pubkey,Option<Option<Pubkey>>,bool,bool)> = (target,su,collect_old,skip) per arm',
 'D1': 'w14a89 vba: validate(..,hb,shared,out:&mut Pubkey)->Result<()> with the in-arm shared override, execute override dropped',
 'D2': 'w14a89 vbb: D1 keeping the execute override',
}
FOLD = {'A2': 'A1', 'A3': 'A1', 'B2': 'B1', 'B2r': 'B1r'}
EVM = {}
for l in open(O + '/w/evm.txt'):
    m = re.match(r'(\S+)\s+---:([-+]\d+) r--:([-+]\d+) -f-:([-+]\d+) rf-:([-+]\d+) rfj:([-+]\d+)', l)
    if m: EVM[m.group(1).replace('__r', '')] = dict(zip(['L---', 'Lr--', 'L-f-', 'Lrf-', 'Lrfj'], map(int, m.groups()[1:])))
rows = []
for k in DESC:
    res = json.load(open(f'{O}/rx/{k}/res.json'))
    r = {'cell': k, 'desc': DESC[k], 'fold': FOLD.get(k), 'ratio': res['ratio'], 'bytes': res['bytes']}
    st = f'{O}/stack/{k}.txt'
    if os.path.exists(st):
        t = open(st).read().split('\n')[0]
        m = re.search(r'\[(.*?)\] \| ph (\{.*?\}) \| phr (\{.*?\})', t)
        if m:
            ph = json.loads(m.group(2)); phr = json.loads(m.group(3))
            r.update({'M_raw': ph['M'], 'Mhc_raw': ph['Mhc'], 'M_rest': phr['M'], 'Mperm_rest': phr['Mperm'], 'Mhc_rest': phr['Mhc'],
                      'restored_livein': m.group(1) or 'none'})
            sc = re.search(r'share (\S+)', t); r['share_call'] = '0x' + sc.group(1).lstrip('0') if sc else None
            ra = re.search(r'^\S+ (\S+) (\d+) M', t); r['ratio_rest'] = float(ra.group(1)); r['bytes_rest'] = int(ra.group(2))
    r.update(EVM.get(k, {}))
    rows.append(r)
json.dump(rows, open(O + '/w/table.json', 'w'), indent=1)
for r in rows:
    print(f"{r['cell']:4s} {r['ratio']:.5f} {r['bytes']} rest {r.get('ratio_rest','')} {r.get('bytes_rest','')} M {r.get('M_raw','-')}/{r.get('M_rest','-')} Mhc {r.get('Mhc_rest','-')} livein {r.get('restored_livein','-')} share {r.get('share_call','-')} | L--- {r.get('L---')} rf- {r.get('Lrf-')} rfj {r.get('Lrfj')} fold {r['fold']}")
