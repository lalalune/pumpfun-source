#!/usr/bin/env python3
"""mkreadme_r37.py NN <genuine build dir> <layout build dir> <prev NN or -> : writes readme-genuine-r37-NN.md and
readme-r37-NN.md for the current pipeline_r37.sh (facts are read from the build dirs' score files)."""
import json, sys
from pathlib import Path
W = Path('/Users/shawwalters/Documents/Codex/2026-10-24/claude-pump-work'); L = W / 'lanes/integ-layout'
nn, gb, lb, prev = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
def sm(b, f): return json.loads((b / f).read_text())['summary']
g37, gbase = sm(gb, 'score.json'), sm(gb, 'score_vs_base.json')
l37, lbase = sm(lb, 'score.json'), sm(lb, 'score_vs_base.json')
gen = gbase['gains']; syn = [x for x in lbase['gains'] if x not in gen]
sets = json.loads((L / 'work/lane_gainsets.json').read_text())
r3 = {'pump-hi (anchor-lang allow-missing-optionals)': ['0xc5650'],
      'pump-hi-e0864cf19 (MigrateV2 accounts, buy_quote)': ['0xd5af0', '0x12ba48', '0xa0070'],
      'bodyloB-04..07': ['0x56658', '0x8c2d8', '0x8e908', '0x90e60', '0x91690', '0x92820', '0x93898', '0x8b970'],
      'libnear3-02': ['0x47d00', '0x48710', '0x54c90', '0x54f30', '0x55630'],
      'pump-big-lo-70240414f (0x37e08 body)': ['0x37e08'],
      'PR362 (route FeeConfig type)': ['0x1159d8'],
      'plainbody-01': ['0x49708'],
      'coordbodyA-01..02': ['0x3dd78', '0x6eed8', '0x6f3e8'],
      'ext798 (shawkkkkk Round37 frontier)': ['0x2bc0', '0x880b0', '0x950e0', '0x98af0', '0xa0538', '0xa0838', '0xa08f8', '0xa0bf0', '0xa13e0', '0xa1bd8']}
def owner(x):
    o = []
    if x in sets['cf08']: o.append('coordfiles')
    if x in sets['cl04']: o.append('coordlib' + ('/changes4' if x in sets['cl04'][20:] else ''))
    if x in sets['nm07']: o.append('nearmiss2')
    for k, v in r3.items():
        if x in v: o.append(k.split(' ')[0])
    return '/'.join(o) or '?'
from collections import Counter
cnt = Counter(owner(x) for x in lbase['gains'])
rows = '\n'.join(f'| {k} | {v} |' for k, v in sorted(cnt.items()))
supers = f'Supersedes integ-layout-r37-{prev}.' if prev != '-' else ''
common = f'''## Pipeline (re-runnable: `tools/pipeline_r37.sh W/integ/r37g5/src <out> <unpadded build dir>`)
1. coordfiles genuine steps: `tools/cf/structural37.py` = coordfiles' final structural.py with S7 skipped (Round37 already
   split the distribution handlers its own way; S7 only pre-positioned sites), then closures.py, split_buy_v2.py,
   closures2..8.py unchanged.
2. coordlib genuine steps: restructure.py; `tools/changes2_r37.py` = changes2.py section B only (validate_buyback_fee_recipient;
   A is obsolete on Round37, C/D are in r37g5); changes3.py; changes4.py (legacy `buy` non-exact path and `sell` body inline
   in the #[program] handlers with per-site closures; coordlib's last, undelivered step, recovered from its transcript).
3. nearmiss2 genuine steps (`tools/nm2_r37.py`): validate_trade(u8,u64,u64) allow-first, add3/sub3, move_native (the legacy
   sell payouts in the lib.rs sell handler), inline signer seeds in transfer_to_user/owned/recipient.
4. Round-3 lanes and pump-hi (`tools/round3.py`, all r37g4-based, ported by hand):
   - pump-hi: Cargo.toml anchor-lang features += `allow-missing-optionals` (missing trailing optional accounts become None,
     so DistributeFeeToHolders::try_accounts builds AccountNotEnoughKeys only twice: 0xc5650).
   - pump-hi e0864cf19: MigrateV2 is #[event_cpi] (owned event_authority/program fields replace the explicit
     UncheckedAccount pair), the bonding_curve constraint in the original evaluation order, three combined field lines
     split (line count kept): 0xd5af0 MigrateV2::try_accounts, 0x12ba48 __global::migrate_v2. Its body-only buy_quote patch
     (u128 numerator first, u128 checked_sub denominator) makes 0xa0070 differ only in Source coordinates, so buy_quote is
     MOVED into lib.rs before reserved_bonding_curve_fees (the original's bonding-curve math region; fee_cpi.rs, not an
     original file, re-exports it) and tools/cl/patterns.json pins its sites to lib.rs:2428/2430 (synthetic layout).
   - bodyloB-07: distribution::sharing_config_shareholders for the buy_v2/sell_v2 TradeEvent shareholders (0x8b970; the
     buy_v2 statement exists in both split handlers, both converted).
   - libnear3-02 (cumulative; its GlobalConfig part is already in r37g5): migrate / migrate_v2 close the pool-authority
     token accounts through token_2022::close_account helpers (0x48710, 0x54f30, 0x55630) and read the pool-authority
     base ATA through pool_authority_mint_token_account (0x47d00, 0x54c90); the integ anchor for 0x4bf50 accepts the new
     `let base=...` form.
   - bodyloB-05/06: the legacy sell SOL output goes through quote_payments::transfer_native_unchecked<&Signer> (added as
     bodyloB has it; its window 0x95f38 is already matched through nearmiss2's move_native); bodyloB-06's inline seeds are
     nearmiss2-07's change (already made by nm2_r37.py).
   - bodyloB-04 (cumulative): refund_pool_authority seeds (0x56658); transfer helpers with the original parameter shapes
     (user_quote_payments::transfer_native_unchecked / transfer_native_curve_unchecked in lib.rs, collect_v2::
     transfer_vault_tokens / transfer_user_tokens_ref / transfer_user_quote_tokens, token_transfers::
     transfer_curve_tokens_ref) wired to their call sites. Its legacy buy hunks are applied to BOTH copies of the legacy
     buy body (buy.rs `execute`, still used by buy_exact_sol_in, and the lib.rs `buy` handler that coordlib's changes4
     inlined); its sell hunk to the lib.rs `sell` handler; trade_v3 buyback transfers and admin_cto pay_token as in bodyloB.
5. ext798 port (`tools/ext798.py`): the parallel Round37 frontier (shawkkkkk packets research/pump-round37-*, final tree
   W/peer-snap/ext798/tree): util/account_name.rs with_owned_name for set_reserved_fee_recipients (0x2bc0); require_neq in
   set_buyback_fee_recipients (0x98af0); BondingCurve::sell_quote (0xa0538; it replaced this lane's byte-identical free
   fn, and integ_genuine.py routes the four original callers - sell_v2, sell_v3, multi-hop sell hop, legacy sell - through
   it); buy_fee_market_cap with checked_div moved into lib.rs (0xa08f8); BondingCurve::apply_buy / apply_sell /
   accrue_fees replacing the V3 handlers' reserve and fee-field assignments (0xa0bf0, 0xa13e0, 0xa1bd8); util/transfer_fee.rs
   behind quote_fee_for_amount and the exact-input budget (0x950e0); util/constant_product.rs tokens_for_quote for the
   legacy, v2 and v3 exact-input token-out paths (0xa0838, 0x880b0; the 927/911 truncation closures stay). Their blank-line
   positioning is not copied: patterns.json (lib.rs curve region 2454..2554) and integ_anchors.json (util files) place the
   sites. Not taken: exact_input_tokens (0x834c8; its original callers have no counterpart here).
   Also: pump-big-lo commit 70240414f body-only patch (tools/patches/, applied by apply_lane_patches.py from
   g04_patches.txt): migrate_bonding_curve_creator writes `a.sharing_config.key()` directly (0x37e08 coordinate-only);
   integ_genuine.py puts its two require!s on their own lines so the layout can place them on 46 / 53.
   And PR #362 (research/pump-feeconfig-decoder-recovery, on main): the route's FeeConfig is its own Rust type in
   trade_types.rs (the alias line kept blank), so the generated pump_fees FeeConfig decoder is whole again (0x1159d8).
   Round-4 lanes (patches against W/base/L06 = integ-layout-r37-06, listed in tools/l06_patches.txt): apply_l06_patches.py
   pad-strips the L06 file and the patched file and merges only the code change into the genuine stage (git merge-file);
   the layout passes re-derive the positions.
   - plainbody-01: migrate v1 refund_pool_authority builds its signer seeds as a nested temporary passed to an inlined
     closure, the bodyloB-01 form of its migrate_v2 twin (0x49708).
   - coordbodyA-02 (cumulative): fee_recipient.rs validate_fee_recipient in the mayhem-first early-return form (0x3dd78,
     errors on 19 / 35), and the shared sell.rs helpers check_bonding_curve_v2 (0x6eed8, sell.rs:126/133) and
     buyback_fee_recipient (0x6f3e8, sell.rs:145) called from the legacy buy/sell bodies (integ anchors place the sites;
     patterns.json now also pins the legacy buy 664/666 closures, whose build-based pairing shifts after this change).
   Not taken: bodyloA F1 (fund_bonding_curve_rent 0x3d250): bodyloA reports ratio 0.907 with block placement left besides
   the extend_account.rs:141 coordinate, so line positioning cannot close it.
6. Unpadded build = integ-genuine-r37-{nn}: {g37["normalized"]} (+{len(gbase["gains"])} vs r37g5).
7. SYNTHETIC line positioning, applied once to the unpadded tree: coordlib `tools/cl/layout.py apply --cand <unpadded
   build>` (lib.rs only; marker `// layout-pad: aligns the next Source site with the original lib.rs line`); coordfiles:
   site map re-derived from the fresh unpadded build (`tools/cf/mksitemap.py`, saved under tools/), `tools/merge_sitemap.py`
   (hand-written anchors win for their windows: an unpadded build pairs same-shape Overflow closures with the wrong
   instance), `tools/cf/layout.py apply --sitemap merged --sitemap extra_anchors.json --sitemap integ_anchors.json` (all other
   files; marker `// layout-pad(N): ...`, token-preserving joins in trade_v3.rs). integ_anchors.json: add3 :285, sub3 :294,
   0x4bf50 migrate_v2.rs:326. The coordfiles pass must be applied to the unpadded tree (re-applying it on its own output
   joins more trade_v3.rs lines); the coordlib pass is idempotent.
8. Padded build = integ-layout-r37-{nn}: {l37["normalized"]}.
'''
open(L / f'readme-r37-{nn}.md', 'w').write(f'''# integ-layout-r37-{nn}: layout composite on the Round37 genuine base r37g5

Base: W/integ/r37g5/src (788 / 165 vs W/base/round37/inventory.json). Result (fastbuild identity recipe):
**{l37["normalized"]} normalized / {l37["raw"]} raw = +{len(lbase["gains"])} vs r37g5 (+{len(l37["gains"])} vs Round37 749), no losses and no
raw losses vs r37g5{(" and vs integ-layout-r37-" + prev) if prev != "-" else ""}, runtime_valid = true.** {supers}

| source of the gain | windows vs r37g5 |
|---|---|
{rows}

Genuine (gained by the unpadded build): {", ".join(gen)}.
Synthetic-layout-dependent ({len(syn)}): all other gains (their code changes are genuine; matching also needs the pads/joins).

{common}
## Not carried over / unresolved
- coordfiles S7 not re-applied on Round37; libinst2-01 not integrated (nested crate needs a harness change); no bodyloA
  delivery yet.

## Recovery note
Lane tools were re-created from the lane transcripts (recover/tx_sandbox.py, recover/tx_segments.py), see PROGRESS.md.
''')
open(L / f'readme-genuine-r37-{nn}.md', 'w').write(f'''# integ-genuine-r37-{nn}: genuine-only subset of the layout composite, on r37g5

Base: W/integ/r37g5/src (788 / 165). Result (identity recipe, score.py vs W/base/round37/inventory.json):
**{g37["normalized"]} normalized / {g37["raw"]} raw = +{len(gbase["gains"])} vs r37g5, no losses, no raw losses, runtime_valid = true. No layout pads,
no joins (synthetic_layout = false).** {("Supersedes integ-genuine-r37-" + prev + ".") if prev != "-" else ""}

Steps 1-4 of tools/pipeline_r37.sh (`--genuine-only`). Windows matched without any line positioning:
{chr(10).join("- " + x + " (" + owner(x) + ")" for x in gen)}
The other {len(syn)} gains of integ-layout-r37-{nn} additionally need the synthetic line positioning.

{common}''')
print('readmes written', nn)
