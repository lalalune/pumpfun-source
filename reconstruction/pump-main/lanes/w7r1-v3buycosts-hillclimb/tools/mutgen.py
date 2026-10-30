#!/usr/bin/env python3
"""Spelling-mutation generator for trade::v3_buy_costs (original 0x80df8).

A configuration picks one spelling per dimension; render() produces the 13 source lines
365..377 of programs/pump/src/trade_v3.rs (fn header .. closing brace) so every error!()
stays on its line (371 total_buyback overflow, 375 net overflow) and nothing else moves.
"""
E = 'error!(PumpError::Overflow)'
SPLIT = 'crate::protocol_fee_split(buyback_bps,{fee},{m})'
PF = 'crate::transfer_fee_recovered::pre_fee_amount(quote_fee,net)'
HDR = ('fn v3_buy_costs(buyback_bps:u64,is_mayhem:u8,quote_fee:&Option<native_transfer_fee::Fee>,quote:u64,'
       'protocol_fee:u64,creator_fee:u64,post:Option<&PostComplete>)->Result<(u64,u64,u64)>{')


def sp(fee, m='is_mayhem!=0'):
    return SPLIT.format(fee=fee, m=m)


PP = 'p.fees.protocol_fee'
# front: buyback + post_buyback (line 366)
FRONT = {
    'F0': f'let buyback={sp("protocol_fee")}.0; let post_buyback=match post{{Some(p)=>{sp(PP)}.0,None=>0}};',
    'F1': f'let buyback={sp("protocol_fee")}.0; let post_buyback=if let Some(p)=post{{{sp(PP)}.0}}else{{0}};',
    'F2': f'let buyback={sp("protocol_fee")}.0; let post_buyback=post.map_or(0,|p|{sp(PP)}.0);',
    'F3': f'let buyback={sp("protocol_fee")}.0; let post_buyback=post.map(|p|{sp(PP)}.0).unwrap_or(0);',
    'F4': f'let (buyback,_)={sp("protocol_fee")}; let post_buyback=match post{{Some(p)=>{{let (b,_)={sp(PP)};b}},None=>0}};',
    'F5': f'let post_buyback=match post{{Some(p)=>{sp(PP)}.0,None=>0}}; let buyback={sp("protocol_fee")}.0;',
    'F6': f'let (buyback,post_buyback)=({sp("protocol_fee")}.0,match post{{Some(p)=>{sp(PP)}.0,None=>0}});',
    'F7': f'let buyback={sp("protocol_fee","is_mayhem>0")}.0; let post_buyback=match post{{Some(p)=>{sp(PP,"is_mayhem>0")}.0,None=>0}};',
    'F8': f'let buyback={sp("protocol_fee")}.0; let post_buyback=post.map(|p|{sp(PP)}.0).unwrap_or_default();',
    'F9': f'let buyback={sp("protocol_fee")}.0; let post_buyback=match post{{None=>0,Some(p)=>{sp(PP)}.0}};',
    'F10': f'let buyback={sp("protocol_fee")}.0; let post_buyback=post.map_or(0,|p|{sp(PP)}.0); let _=&post_buyback;',
    'F11': f'let split=|fee:u64|{sp("fee")}.0; let buyback=split(protocol_fee); let post_buyback=match post{{Some(p)=>split({PP}),None=>0}};',
}

W = 'fn s(b:u64,f:u64,m:bool)->u64{crate::protocol_fee_split(b,f,m).0}'
PBW = 'fn pb(b:u64,post:Option<&PostComplete>,m:bool)->u64{match post{Some(p)=>crate::protocol_fee_split(b,p.fees.protocol_fee,m).0,None=>0}}'
for tag, attr in (('i', '#[inline]'), ('n', ''), ('a', '#[inline(always)]'), ('x', '#[inline(never)]')):
    FRONT['FW' + tag] = f'{attr}{W} let buyback=s(buyback_bps,protocol_fee,is_mayhem!=0); let post_buyback=match post{{Some(p)=>s(buyback_bps,{PP},is_mayhem!=0),None=>0}};'
    FRONT['FP' + tag] = f'{attr}{W} let buyback={sp("protocol_fee")}.0; let post_buyback=match post{{Some(p)=>s(buyback_bps,{PP},is_mayhem!=0),None=>0}};'
    FRONT['FQ' + tag] = f'{attr}{W} let buyback=s(buyback_bps,protocol_fee,is_mayhem!=0); let post_buyback=match post{{Some(p)=>{sp(PP)}.0,None=>0}};'
    FRONT['FB' + tag] = f'{attr}{PBW} let buyback={sp("protocol_fee")}.0; let post_buyback=pb(buyback_bps,post,is_mayhem!=0);'
# total_buyback (370 head / 371 tail with error!)
TOTAL = {
    'T0': ('let total_buyback=buyback.checked_add(post_buyback)', f'.ok_or_else(||{E})?;'),
    'T1': ('let total_buyback=match buyback.checked_add(post_buyback){Some(v)=>v,', f'None=>return Err({E})}};'),
    'T2': ('let Some(total_buyback)=buyback.checked_add(post_buyback) else{', f'return Err({E})}};'),
    'T3': ('let total_buyback=buyback.checked_add(post_buyback).ok_or(())', f'.map_err(|_|{E})?;'),
    'T4': ('let (total_buyback,o)=buyback.overflowing_add(post_buyback);', f'if o{{return Err({E})}}'),
    'T5': ('let total_buyback=post_buyback.checked_add(buyback)', f'.ok_or_else(||{E})?;'),
    'T6': ('let total_buyback=if let Some(v)=buyback.checked_add(post_buyback){v}else{', f'return Err({E})}};'),
    'T7': ('let total_buyback=buyback.checked_add(post_buyback).map_or_else(||Err(', f'{E}),Ok)?;'),
    'T8': ('let total_buyback=match buyback.checked_add(post_buyback){None=>', f'return Err({E}),Some(v)=>v}};'),
}
A3 = 'add3(quote,protocol_fee,creator_fee)'
B3 = 'add3(p.quote_in,p.fees.protocol_fee,p.fees.creator_fee)'
FIRST = {
    'A0': f'let first={A3}?;',
    'A1': f'let first=match {A3}{{Ok(v)=>v,Err(e)=>return Err(e)}};',
    'A2': f'let first={A3}; let first=first?;',
}
SECOND = {
    'B0': f'let second=if let Some(p)=post{{{B3}?}}else{{0}};',
    'B1': f'let second=match post{{Some(p)=>{B3}?,None=>0}};',
    'B2': f'let second=post.map(|p|{B3}).transpose()?.unwrap_or(0);',
    'B3': f'let second=post.map_or(Ok(0),|p|{B3})?;',
    'B4': f'let second=match post{{None=>0,Some(p)=>{B3}?}};',
    'B5': f'let second=if let Some(p)=post{{match {B3}{{Ok(v)=>v,Err(e)=>return Err(e)}}}}else{{0}};',
}
SUMSUB = 'first.checked_add(second).and_then(|sum|sum.checked_sub(total_buyback))'
# net (374 head / 375 tail with error!); third item: True when quote_transfer_fee already bound
NET = {
    'N0': (f'let (pool_quote,net)={SUMSUB}', f'.ok_or_else(||{E}).and_then(|net|{PF}.map(|g|(g,net)))?;', False),
    'N1': (f'let net={SUMSUB}', f'.ok_or_else(||{E})?; let pool_quote={PF}?;', False),
    'N2': ('let net=match first.checked_add(second){Some(s) if s>=total_buyback=>s-total_buyback,', f'_=>return Err({E})}}; let pool_quote={PF}?;', False),
    'N3': (f'let net={SUMSUB}', f'.ok_or_else(||{E})?; let (pool_quote,quote_transfer_fee)=gross_up_quote(quote_fee,net)?;', True),
    'N5': (f'let (pool_quote,net)=match {SUMSUB}{{Some(net)=>({PF}?,net),', f'None=>return Err({E})}};', False),
    'N6': ('let (pool_quote,net)=first.checked_add(second).and_then(|sum|(sum>=total_buyback).then(||sum-total_buyback))', f'.ok_or_else(||{E}).and_then(|net|{PF}.map(|g|(g,net)))?;', False),
    'N7': ('let (pool_quote,net)=second.checked_add(first).and_then(|sum|sum.checked_sub(total_buyback))', f'.ok_or_else(||{E}).and_then(|net|{PF}.map(|g|(g,net)))?;', False),
    'N8': (f'let (pool_quote,net)={SUMSUB}', f'.ok_or_else(||{E}).and_then(|net|Ok(({PF}?,net)))?;', False),
    'N9': (f'let (pool_quote,net)={SUMSUB}', f'.ok_or_else(||{E}).and_then(|net|{PF}.map(|g|(g,net))).map_err(core::convert::identity)?;', False),
    'N10': (f'let (pool_quote,net)={SUMSUB}', f'.ok_or_else(||{E}).and_then(|net|match {PF}{{Ok(g)=>Ok((g,net)),Err(e)=>Err(e)}})?;', False),
    'N11': (f'let (pool_quote,net)={SUMSUB}', f'.ok_or_else(||{E}).map(|net|({PF},net)).and_then(|(g,net)|g.map(|g|(g,net)))?;', False),
    'N12': (f'let pq={SUMSUB}', f'.ok_or_else(||{E}).and_then(|net|{PF}.map(|g|(g,net))); let (pool_quote,net)=pq?;', False),
}
QQ = 'pool_quote.checked_sub(net)'
FINAL = {
    'Q0': f'let quote_transfer_fee={QQ}.ok_or_else(gross_up_quote_error)?; Ok((pool_quote,total_buyback,quote_transfer_fee))',
    'Q1': f'Ok((pool_quote,total_buyback,{QQ}.ok_or_else(gross_up_quote_error)?))',
    'Q2': f'match {QQ}{{Some(f)=>Ok((pool_quote,total_buyback,f)),None=>Err(gross_up_quote_error())}}',
    'Q3': f'let quote_transfer_fee={QQ}.ok_or_else(||gross_up_quote_error())?; Ok((pool_quote,total_buyback,quote_transfer_fee))',
    'Q4': f'{QQ}.map(|f|(pool_quote,total_buyback,f)).ok_or_else(gross_up_quote_error)',
    'Q5': f'let Some(quote_transfer_fee)={QQ} else{{return Err(gross_up_quote_error())}}; Ok((pool_quote,total_buyback,quote_transfer_fee))',
    'Q6': f'{QQ}.ok_or_else(gross_up_quote_error).map(|f|(pool_quote,total_buyback,f))',
}
ORDER = ['O0', 'O1', 'O2']
DIMS = {'F': FRONT, 'T': TOTAL, 'A': FIRST, 'B': SECOND, 'N': NET, 'Q': FINAL, 'O': {k: k for k in ORDER}}
BASE = {'F': 'F0', 'T': 'T0', 'A': 'A0', 'B': 'B0', 'N': 'N0', 'Q': 'Q0', 'O': 'O0'}


def key(cfg):
    return '-'.join(cfg[d] for d in 'FTABNQO')


def parse(k):
    parts = k.split('-')
    return dict(zip('FTABNQO', parts))


def render(cfg):
    """Return the 13 lines for 365..377."""
    L = {n: '' for n in range(365, 378)}
    L[365] = HDR
    L[377] = '}'
    L[366] = '    ' + FRONT[cfg['F']]
    th, tt = TOTAL[cfg['T']]
    a = FIRST[cfg['A']]
    b = SECOND[cfg['B']]
    nh, nt, has_q = NET[cfg['N']]
    q = 'Ok((pool_quote,total_buyback,quote_transfer_fee))' if has_q else FINAL[cfg['Q']]
    o = cfg['O']
    if o == 'O0':
        L[370], L[371], L[372], L[373] = '    ' + th, '        ' + tt, '    ' + a, '    ' + b
    elif o == 'O1':  # add3 calls before total_buyback
        L[367], L[368] = '    ' + a, '    ' + b
        L[370], L[371] = '    ' + th, '        ' + tt
    elif o == 'O2':  # first before total_buyback, second after
        L[367] = '    ' + a
        L[370], L[371], L[373] = '    ' + th, '        ' + tt, '    ' + b
    L[374], L[375], L[376] = '    ' + nh, '        ' + nt, '    ' + q
    return [L[n] for n in range(365, 378)]


def neighbors(cfg):
    for d, opts in DIMS.items():
        for v in opts:
            if v != cfg[d]:
                c = dict(cfg)
                c[d] = v
                if d == 'Q' and NET[c['N']][2] and c['Q'] != 'Q0':
                    continue
                yield c


if __name__ == '__main__':
    import sys
    cfg = parse(sys.argv[1]) if len(sys.argv) > 1 else BASE
    print('\n'.join(render(cfg)))
