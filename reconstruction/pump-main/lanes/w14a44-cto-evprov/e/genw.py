#!/usr/bin/env python3
"""genw.py: wallet CollectCreatorFeeEvent literal variants (line 564): name=<literal body after 'let e='> pairs below."""
import os, json
E = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a44-cto-evprov/e')
LIT = 'let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator:a.current_creator.key(),creator_fee:collected,quote_mint};'
V = {
 'w_qmk': 'let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator:a.current_creator.key(),creator_fee:collected,quote_mint:a.quote_mint.key()};',
 'w_crd': 'let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator:*a.current_creator.key,creator_fee:collected,quote_mint};',
 'w_crctx': 'let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator:ctx.accounts.current_creator.key(),creator_fee:collected,quote_mint};',
 'w_o_cfq': 'let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator_fee:collected,creator:a.current_creator.key(),quote_mint};',
 'w_o_qcf': 'let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,quote_mint,creator:a.current_creator.key(),creator_fee:collected};',
 'w_o_tlast': 'let e=CollectCreatorFeeEvent{creator:a.current_creator.key(),creator_fee:collected,quote_mint,timestamp:Clock::get()?.unix_timestamp};',
 'w_tspre': 'let timestamp=Clock::get()?.unix_timestamp;let e=CollectCreatorFeeEvent{timestamp,creator:a.current_creator.key(),creator_fee:collected,quote_mint};',
 'w_clk': 'let clock=Clock::get()?;let e=CollectCreatorFeeEvent{timestamp:clock.unix_timestamp,creator:a.current_creator.key(),creator_fee:collected,quote_mint};',
 'w_tsmap': 'let e=CollectCreatorFeeEvent{timestamp:Clock::get().map(|c|c.unix_timestamp)?,creator:a.current_creator.key(),creator_fee:collected,quote_mint};',
}
for n, v in V.items():
    open(f'{E}/{n}.py', 'w').write('EDITS=' + json.dumps([[LIT, v]]) + '\n'); print(n)
