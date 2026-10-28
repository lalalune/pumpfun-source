#!/usr/bin/env python3
"""closures2.py <crate dir>: second batch of inline closures (coordfiles lane).
  trade_v3.rs  811 T  buy_v3: u64::try_from(curve buy quote)             (orig 0x147ba0 +0x720, after lib.rs:2428 helper)
               1140 T sell_v3: u64::try_from(curve sell quote)           (orig 0x14a8a8 +0x640, after lib.rs:2454 helper)
               1155 O sell_v3: transfer fee = output - net_output        (orig 0x14a8a8 +0x7b8, after util/transfer_fee.rs:56)
  sell_v2.rs   386 O  transfer fee = output - net_output after the TooLittleSolReceived check at 379
               (orig 0x144508 +0x1ae0: `jlt [output], [net]` after W0x950e0 = util/transfer_fee.rs:56)
The net output is bound once (net_output) and the fee re-derived from it exactly as the original does;
values are unchanged (fee = output - (output - fee)).
"""
import sys
from pathlib import Path
S = Path(sys.argv[1]) / 'src'
def rep(p, old, new):
    f = S / p; t = f.read_text()
    assert t.count(old) == 1, (p, old[:90], t.count(old))
    f.write_text(t.replace(old, new))
rep('trade_v3.rs', '    let quote=narrow(quotient.checked_add(1).ok_or_else(||error!(PumpError::Overflow))?)?;\n',
    '    let quote=u64::try_from(quotient.checked_add(1).ok_or_else(||error!(PumpError::Overflow))?).map_err(|_|error!(PumpError::Truncation))?;\n')
rep('trade_v3.rs', '    let quote=narrow(amount as u128*curve.virtual_quote_reserves as u128/(curve.virtual_token_reserves as u128+amount as u128))?;\n',
    '    let quote=u64::try_from(amount as u128*curve.virtual_quote_reserves as u128/(curve.virtual_token_reserves as u128+amount as u128)).map_err(|_|error!(PumpError::Truncation))?;\n')
rep('trade_v3.rs', '    require_gte!(sub(user_output,quote_transfer_fee)?,min_sol_output,PumpError::TooLittleSolReceived);\n',
    '    let net_output=sub(user_output,quote_transfer_fee)?;\n'
    '    require_gte!(net_output,min_sol_output,PumpError::TooLittleSolReceived);\n'
    '    let quote_transfer_fee=user_output.checked_sub(net_output).ok_or_else(||error!(PumpError::Overflow))?;\n')
rep('sell_v2.rs', ' require_gte!(sub(output,quote_transfer_fee)?,minimum,PumpError::TooLittleSolReceived);\n',
    ' let net_output=sub(output,quote_transfer_fee)?;\n'
    ' require_gte!(net_output,minimum,PumpError::TooLittleSolReceived);\n'
    ' let quote_transfer_fee=output.checked_sub(net_output).ok_or_else(||error!(PumpError::Overflow))?;\n')
print('closures2 applied')
