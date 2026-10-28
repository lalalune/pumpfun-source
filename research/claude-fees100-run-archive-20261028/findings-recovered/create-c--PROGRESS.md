# recovered from the transcript of lane create-c (PROGRESS.md); entries in order

# create-c lane PROGRESS (sibling-analogy strategy)
Target: orig window 163920 (create_donation_fee_pda::create, 13800 B / 1641 insns) + eliminate extra
<DonationFeePdaCreated as Event>::data body (648 B).
Lane dir: R/lanes/create-c ; src = clone of w582 ; target = warm native target ; outputs in out/.
## Status
- 11:47 lane set up; baseline build pending.

# create-c lane PROGRESS (sibling-analogy strategy) — resume from here
Target: orig window 163920 (create_donation_fee_pda::create, 13800 B / 1641 insns) + eliminate extra
<DonationFeePdaCreated as Event>::data body. FRONTIER = w583 (R/shared/frontier/w583). Baseline native w583 (579).
Tools: lanes/create-c/tools/{place.py (line-placed template renderer), an.sh (dis+calls+blocks), blocks.py,
pattern.sh (per-line Display-inlined W / ToString-outlined C; orig = 148W 152W 156C 174C 192W 197C 204C 213C 214C 221W),
border.py (block alignment), irorder.py/llfn.py (IR block order)}. Generators: lanes/create-c/gen/{common.py,gen1.py,gen2.py}
-> overlays in lanes/create-c/fv/<name>/... ; build+score: python3 -I R/shared/tools/farm.py --base R/shared/frontier/w583
--out lanes/create-c/farm1 --addr 163920 --parallel 3 name=lanes/create-c/fv/name
## Best so far
- p3 (lanes/create-c/fv/p3): helper `fn get_creator_and_quote_mint(&Account<BC>, &UncheckedAccount, &InterfaceAccount<Mint>,
  &UncheckedAccount, &Signer) -> Result<(Pubkey,Pubkey)>` + `fn is_graduated(&BondingCurve)->bool`; deferred-init
  `let creator; let quote_mint; if is_graduated(curve) { pool arm } else { curve arm }` ; sharing/else returns Ok((..));
  create(): disabled/exists checks, helper(...)?, state writes, event from account keys, emit!/emit_cpi!.
  ratio 0.7574 span 600, exact callee multiset, exact warm/cold pattern, exact reserve-test layout. No losses.
## Next
- analyze p3 residual (border.py), sharing-path structure (orig: sharing errors+success share Ref drop + flag dispatch at 12304),
  deser-OK trampoline at 720 (orig `ja ->4784`), state-write/event ordering, register allocation.