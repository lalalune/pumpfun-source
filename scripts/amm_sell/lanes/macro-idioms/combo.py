#!/usr/bin/env python3
"""combo.py NAME H T K : build src/NAME.rs from pristine+owner_ne with head H (467/468), tail T (479/480), key K (464)."""
import sys
P='$HOME/Documents/Codex/2026-10-24/amm-sell-swarm/baselines/pristine-ws/programs/pump-amm/src/instructions/swap/sell.rs'
E='PumpAmmError::InvalidCashbackAccumulatorAta'; EA=f'return err!({E});'; I='    '
H={
 'b2':  (f'{I}if ata.is_writable == false {{ {EA} }}', f'{I}if ata.data_is_empty() {{'),
 'e0':  (f'{I}if !ata.is_writable {{ {EA} }} else if ata.data_is_empty() {{', ''),
 'e0f': (f'{I}if ata.is_writable == false {{ {EA} }} else if ata.data_is_empty() {{', ''),
 'emptythen': (f'{I}if ata.is_writable {{}} else {{ {EA} }}', f'{I}if ata.data_is_empty() {{'),
 'matchF': (f'{I}match ata.is_writable {{ false => {EA[:-1]}, true => {{}} }}', f'{I}if ata.data_is_empty() {{'),
 'matchT': (f'{I}match ata.is_writable {{ true => {{}} false => {EA[:-1]}, }}', f'{I}if ata.data_is_empty() {{'),
 'letelse': (f'{I}let true = ata.is_writable else {{ {EA} }};', f'{I}if ata.data_is_empty() {{'),
 'iflet': (f'{I}if let false = ata.is_writable {{ {EA} }}', f'{I}if ata.data_is_empty() {{'),
 'matches': (f'{I}if matches!(ata.is_writable, false) {{ {EA} }}', f'{I}if ata.data_is_empty() {{'),
 'notnot': (f'{I}if !ata.is_writable == true {{ {EA} }}', f'{I}if ata.data_is_empty() {{'),
 'bitxor': (f'{I}if ata.is_writable ^ true {{ {EA} }}', f'{I}if ata.data_is_empty() {{'),
 'eqfalse_rev': (f'{I}if false == ata.is_writable {{ {EA} }}', f'{I}if ata.data_is_empty() {{'),
 'e0emptythen': (f'{I}if ata.is_writable {{}} else {{ {EA} }}', f'{I}if ata.data_is_empty() {{'),
}
T={'q': (f'{I}{I}))?;', f'{I}}}'), 'ok': (f'{I}{I}))', f'{I}}} else {{ Ok(()) }}?;'), 'el': (f'{I}{I}))?;', f'{I}}} else {{}}')}
K={'req': None, 'ne': f'{I}if ata.key() != expected_ata {{ {EA} }}'}
name,h,t,k=sys.argv[1:5]
L=open(P).read().split('\n')
L[443]='        if *user_volume_accumulator.owner != crate::ID { return err!(PumpAmmError::InvalidCashbackAccumulator); }'
L[466],L[467]=H[h]
L[478],L[479]=T[t]
if K[k]: L[463]=K[k]
open(f'src/{name}.rs','w').write('\n'.join(L))
print(f'src/{name}.rs')
