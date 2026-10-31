# w14a95-cto-devol334: replace the line-334 `read_volatile(holder_key)` placeholder (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: find ordinary source that replaces the `unsafe{core::ptr::read_volatile(holder_key ..)}` placeholder that #3430
put before line 334's `if !st.fee_configurable` (+8 B, +1 M pure fill), keeping line 338's placeholder (lane devol338).
Ledger approach `devol334`, keys `0x22a10-w14-<main7>-devol334-<variant>-v1`.

`M` = matched masked tokens, `ratio = 2M / (3339 + bytes/8 - 88)`. All numbers are raw-IR capture + `opt -O3` + `llc`
(w14a88/w14a73 `capvar.sh` + `rx.py`; `capraw2.py` = IR-only capture). The oracle reproduces main's metric.

## Result: negative. No ordinary spelling ties the placeholder.

| base | bytes | M | ratio |
| --- | ---: | ---: | ---: |
| main ecea702 (with vol334) | 27,400 | 2,239 | 0.67076 |
| B0 = ecea702 minus vol334 | 27,392 | 2,238 | 0.67056 |
| main 963d1ee (#3437, with vol334) | 27,400 | 2,244 | 0.67226 |
| B1 = 963d1ee minus vol334 | 27,392 | 2,243 | 0.67206 |

To tie, a replacement must be exactly +8 B and M-neutral (B0: >= 2,239 at 27,400; B1: >= 2,244 at 27,400).
Nothing in about 140 variants does that (tables below).

## What the placeholder is

- In post-opt IR it is a dead `load volatile i8, ptr %holder_key` at the head of `bb54.i` (the fee_configurable test).
  `llc` keeps it as `ldxb r1,[r10-0x6a0]` at the top of LBB0_48, right before `ldxdw r1,[r10-0x948]; jeq r1,0`
  (reload of the spilled `fee_configurable` byte). The original has no load there: its 334 test is
  `ldxdw r1,[r10-0x940]; jeq r1,0,+0x1d` (orig 0x24048).
- volscan on B1 (`tools/volscan.py` from w14a88: one volatile load at each of the 280 execute block heads): the same 35
  blocks as on 95a64ba reach M 2,244 (= main), none higher. So pure +8 fill can only tie main.
- `!st.fee_configurable` -> `st.fee_configurable==false` (or `!=true`) is the only ordinary +8 B form at 334 itself, but
  it is not fill: MIR emits the success block first, `bb58.i` (fee range test) is laid out before `bb59.i` (the 334
  error block), and the extra 8 B are a jump. M 2,196 (-42) on B0.
- Removing line 338's placeholder as well costs 22 M on 963d1ee (X0: 27,384, M 2,221), so 338 is a structural lever,
  not fill; the +16 B `inline-L339-6` repay does not bring it back (X1: 27,400, M 2,221).

## Leads for other lanes (B1 = 963d1ee minus vol334, 27,392 B, M 2,243)

- `inline-L339-6` (shared non-holder arm `target=a.bonding_curve.creator;((false,Some(args.0),true))` instead of
  `let r=(..);target=..;r`): **+16 B, +1 M** (27,408, M 2,244). Natural (drops the `let r` temporary), but every -8 B knob
  paired with it loses 4-9 M (table). It needs a faithful -8 B knob that is M-neutral on top of it.
- `iflet-L746-0s/1n` (sharing CPI back to `match`): +8 B, M 2,242 at 27,400 (-1 vs the bound).
- `unwrapor-L757-0u` (`curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps)`): +8 B, M 2,241 at 27,400.
- `ifq-L556-0e/1t` (wallet `if collect_old{wallet(&ctx)}else{Ok(())}?` / `.then().transpose()?`): -8 B, -4 M.


## Screen on B0 (ecea702 minus vol334: 27,392 B, M 2,238; tie = 27,400 B / M 2,239)

| variant | bytes | dB | M | dM | edit |
| --- | ---: | ---: | ---: | ---: | --- |
| andand-L289-0 | 26584 | -808 | 1577 | -661 | `st.holder_reward&&!(hopt==Some(true))` -> `(st.holder_reward)&(!(hopt==Some(true)))` |
| andand-L296-0 | 26952 | -440 | 1404 | -834 | `holder&&!st.holder_reward` -> `(holder)&(!st.holder_reward)` |
| not-L334-0f0 | 27400 | +8 | 2196 | -42 | `!st.fee_configurable` -> `(st.fee_configurable==false)` |
| not-L334-1f1 | 27400 | +8 | 2196 | -42 | `!st.fee_configurable` -> `(st.fee_configurable!=true)` |
| andand-L296-1 | 27400 | +8 | 2110 | -128 | `!st.holder_reward&&!st.holder_enabled` -> `(!st.holder_reward)&(!st.holder_enabled)` |
| andand-L339-0 | 27408 | +16 | 1916 | -322 | `a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owne` -> `(a.sharing_config.key()==a.bonding_curve.creator)&(a.sharing_config.ow` |
| p_evL | 27392 | +0 | 2238 | +0 | `event_authority:AccountInfo{data:a.pump_fees_event_authority.data.clon` -> `event_authority:AccountInfo{lamports:a.pump_fees_event_authority.lampo` |
| match-L326-0i | 27400 | +8 | 2153 | -85 | `match fee{Some(f)=>{if st.quote_locked{return Err(error!(PumpError::Cr` -> `if let Some(f)=fee{if st.quote_locked{return Err(error!(PumpError::Cre` |
| h_sk_inl | 27352 | -40 | 2069 | -169 | `let args=&(new,);let sk=a.sharing_config.key();let mut target=validate` -> `let args=&(new,);let mut target=validate(&st,hopt,fee,new,&holder_key,` |
| h_sk_first | 27224 | -168 | 2179 | -59 | `let args=&(new,);let sk=a.sharing_config.key();let mut target=validate` -> `let sk=a.sharing_config.key();let args=&(new,);let mut target=validate` |
| h_hk_dot0 | 27392 | +0 | 1865 | -373 | `let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards"` -> `let holder_key=Pubkey::find_program_address(&[b"holder-rewards",mint.a` |
| h_hk_tup | 27392 | +0 | 1865 | -373 | `let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards"` -> `let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mi` |
| not-L296-0f0 | 27400 | +8 | 1412 | -826 | `er&&!st.holder_reward&&!s` -> `er&&(st.holder_reward==false)&&!s` |
| not-L296-2f0 | 27400 | +8 | 1431 | -807 | `!st.holder_enabled` -> `(st.holder_enabled==false)` |
| h_hk_ref | 27392 | +0 | 2237 | -1 | `let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards"` -> `let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()]` |
| h_fr_not | 27392 | +0 | 2238 | +0 | `if f==0\|\|f>st.max_fee{` -> `if !(f>0&&f<=st.max_fee){` |
| h_fr_split | 27600 | +208 | 1851 | -387 | `if f==0\|\|f>st.max_fee{return Err(error!(PumpError::CreatorFeeBpsOutOfR` -> `if f==0{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}if f>s` |
| h_fc_else | 27392 | +0 | 2238 | +0 | `if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConf` -> `if st.fee_configurable{}else{return Err(error!(PumpError::CreatorFeeNo` |
| h_ik_split | 27384 | -8 | 1879 | -359 | `if t==*sharing\|\|t==*holder_key{return Err(error!(PumpError::InvalidCre` -> `if t==*sharing{return Err(error!(PumpError::InvalidCreator));}if t==*h` |
| h_ik_ref | 27392 | +0 | 2238 | +0 | `if t==*sharing\|\|t==*holder_key{` -> `if &t==sharing\|\|&t==holder_key{` |
| h_z_ne | 27392 | +0 | 2238 | +0 | `if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotB` -> `if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotB` |
| h_tg_okor | 27304 | -88 | 2091 | -147 | `let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCre` -> `let t=new.ok_or_else(\|\|error!(PumpError::CtoNewCreatorRequired))?;` |
| h_nw_ne | 27392 | +0 | 2238 | +0 | `if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed)` -> `if new!=None{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}` |
| h_mx_local | 27392 | +0 | 2238 | +0 | `if f==0\|\|f>st.max_fee{` -> `let max=st.max_fee;if f==0\|\|f>max{` |
| p_nC | 27408 | +16 | 2240 | +2 | `let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;` -> `let nf=a.bonding_curve.creator_fee_bps;let pool_updated=!a.pool.data_i` (+1 more) |
| p_cu_replace | 27392 | +0 | 2238 | +0 | `let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;` -> `let old_creator=core::mem::replace(&mut curve.creator,target);let old_` (+1 more) |
| not-L559-0f0 | 27400 | +8 | 2187 | -51 | `!a.creator_vault_quote_token_account.data_is_empty()` -> `(a.creator_vault_quote_token_account.data_is_empty()==false)` |
| not-L559-1f1 | 27400 | +8 | 2187 | -51 | `!a.creator_vault_quote_token_account.data_is_empty()` -> `(a.creator_vault_quote_token_account.data_is_empty()!=true)` |
| not-L556-0f0 | 27400 | +8 | 2236 | -2 | `!a.current_creator.is_writable` -> `(a.current_creator.is_writable==false)` |
| ifq-L561-0e | 27400 | +8 | 2235 | -3 | `if !collection_native\|\|coin_present{anchor_spl::associated_token::crea` -> `if !collection_native\|\|coin_present{anchor_spl::associated_token::crea` |
| inline-L314-0 | 27384 | -8 | 2023 | -215 | `let cashback=if holder{false}else{st.cashback};             match fee{` -> `match fee{Some(f)=>{if st.quote_locked{return Err(error!(PumpError::Cr` |
| unwrapor-L757-0u | 27400 | +8 | 2236 | -2 | `if let Some(f)=fee{curve.creator_fee_bps=f;}` -> `curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps);` |
| not-L561-0f0 | 27400 | +8 | 2235 | -3 | `!collection_native` -> `(collection_native==false)` |
| oror-L339-1 | 27352 | -40 | 2050 | -188 | `q==anchor_spl::token::spl_token::native_mint::ID\|\|a.global.whitelisted` -> `(q==anchor_spl::token::spl_token::native_mint::ID)\|(a.global.whitelist` |

## Screen on B1 (963d1ee minus vol334: 27,392 B, M 2,243; tie = 27,400 B / M 2,244)

| variant | bytes | dB | M | dM | edit |
| --- | ---: | ---: | ---: | ---: | --- |
| unwrapor-L757-0u | 27400 | +8 | 2241 | -2 | `if let Some(f)=fee{curve.creator_fee_bps=f;}` -> `curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps);` |
| k_ev_cb_local | 27400 | +8 | 2236 | -7 | `is_cashback_coin:a.bonding_curve.is_cashback_coin,` -> `is_cashback_coin:cashback,` |
| not-L561-0f0 | 27400 | +8 | 2240 | -3 | `!collection_native` -> `(collection_native==false)` |
| ifq-L561-0e | 27400 | +8 | 2240 | -3 | `if !collection_native\|\|coin_present{anchor_spl::associated_token::crea` -> `if !collection_native\|\|coin_present{anchor_spl::associated_token::crea` |
| letswap-L339-0 | 27408 | +16 | 2156 | -87 | `let mint=a.mint.key();let shared=a.sharing_config.key()==a.bonding_cur` -> `let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_` |
| oror-L561-0 | 27408 | +16 | 2226 | -17 | `!collection_native\|\|coin_present` -> `(!collection_native)\|(coin_present)` |
| inline-L339-6 | 27408 | +16 | 2244 | +1 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;((false,Some(args.0),true))` |
| reread-L664-0amount | 27416 | +24 | 2237 | -6 | `(if amount>0{c` -> `(if (a.creator_vault.lamports().saturating_sub(min))>0{c` |
| k_g_w_clock_local | 27408 | +16 | 2240 | -3 | `let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,` -> `let ts=Clock::get()?.unix_timestamp;let e=CollectCreatorFeeEvent{times` |
| andand-L339-0 | 27408 | +16 | 1861 | -382 | `a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owne` -> `(a.sharing_config.key()==a.bonding_curve.creator)&(a.sharing_config.ow` |
| ifq-L556-0e | 27384 | -8 | 2239 | -4 | `if collect_old{wallet(&ctx)?;}` -> `if collect_old{wallet(&ctx)}else{Ok(())}?;` |
| k_wl_ts_clockvar | 27408 | +16 | 2240 | -3 | `let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,` -> `let clock=Clock::get()?;let e=CollectCreatorFeeEvent{timestamp:clock.u` |
| iflet-L757-0s | 27384 | -8 | 2238 | -5 | `if let Some(f)=fee{curve.creator_fee_bps=f;}` -> `match fee{Some(f)=>{curve.creator_fee_bps=f;}None=>{}}` |
| ifq-L556-1t | 27384 | -8 | 2239 | -4 | `if collect_old{wallet(&ctx)?;}` -> `collect_old.then(\|\|wallet(&ctx)).transpose()?;` |
| reread-L578-0coin_p | 27384 | -8 | 2230 | -13 | `if coin_present&do_` -> `if (!a.coin_creator_vault_ata.data_is_empty())&do_` |
| issome-L767-1f1 | 27384 | -8 | 2205 | -38 | `sharing_update.is_some()` -> `(sharing_update!=None)` |
| k_rL | 27384 | -8 | 2238 | -5 | `lamports:a.pump_fees.lamports.clone(),` -> `lamports:x.lamports.clone(),` |
| k_L_fee_unwrap_again | 27400 | +8 | 2227 | -16 | `if let Some(f)=fee{curve.creator_fee_bps=f;}` -> `curve.creator_fee_bps=fee.unwrap_or(old_fee);` |
| k_tp | 27384 | -8 | 2236 | -7 | `let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;` -> `let pool_updated=a.pool.data_len()!=0 && a.pool.owner==&AMM;` |
| k_nO | 27384 | -8 | 2234 | -9 | `owner:a.creator_vault_quote_token_account.owner,` -> `owner:x.owner,` |
| iflet-L746-1n | 27400 | +8 | 2242 | -1 | `if let Some(val)=sharing_update{     crate::pump_fees::cpi::admin_cto_` -> `match sharing_update{None=>{}Some(val)=>{     crate::pump_fees::cpi::a` |
| iflet-L746-0s | 27400 | +8 | 2242 | -1 | `if let Some(val)=sharing_update{     crate::pump_fees::cpi::admin_cto_` -> `match sharing_update{Some(val)=>{     crate::pump_fees::cpi::admin_cto` |
| ifq-L746-1t | compile/none | | | | `if let Some(val)=sharing_update{     crate::pump_fees::cpi::admin_cto_` -> `(let Some(val)=sharing_update).then(\|\|     crate::pump_fees::cpi::admi` |
| ifq-L746-0e | 27392 | +0 | 2243 | +0 | `if let Some(val)=sharing_update{     crate::pump_fees::cpi::admin_cto_` -> `if let Some(val)=sharing_update{     crate::pump_fees::cpi::admin_cto_` |
| letswap-L761-1 | 27448 | +56 | 2105 | -138 | `let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;let par` -> `let pargs=(target,a.bonding_curve.is_holder_reward,fee);let pool_updat` |
| inline-L761-0 | 27376 | -16 | 2236 | -7 | `let nf=a.bonding_curve.creator_fee_bps;let pool_updated=!a.pool.data_i` -> `let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;let par` |
| andand-L339-3 | 27424 | +32 | 1861 | -382 | `!st.holder_reward&&st.creator!=Pubkey::default()` -> `(!st.holder_reward)&(st.creator!=Pubkey::default())` |
| andand-L339-1 | 27312 | -80 | 2035 | -208 | `a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty()` -> `(a.sharing_config.owner==&FEES)&(!a.sharing_config.data_is_empty())` |
| cmpneg-L289-0 | 27392 | +0 | 2243 | +0 | `&&!(hopt==Some(true)){re` -> `&&!(!(hopt!=Some(true))){re` |
| I6+ifq-L556-1t | 27400 | +8 | 2239 | -4 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;((false,Some(args.0),true))` (+1 more) |
| I6+ifq-L556-0e | 27400 | +8 | 2239 | -4 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;((false,Some(args.0),true))` (+1 more) |
| I6+iflet-L757-1n | 27400 | +8 | 2238 | -5 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;((false,Some(args.0),true))` (+1 more) |
| I6+iflet-L757-0s | 27400 | +8 | 2238 | -5 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;((false,Some(args.0),true))` (+1 more) |
| I6+k_tp | 27400 | +8 | 2236 | -7 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;((false,Some(args.0),true))` (+1 more) |
| I6+k_rL | 27400 | +8 | 2238 | -5 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;((false,Some(args.0),true))` (+1 more) |
| I6+iflet-L746-0s | 27416 | +24 | 2241 | -2 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;((false,Some(args.0),true))` (+1 more) |
| I6+k_nO | 27400 | +8 | 2234 | -9 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;((false,Some(args.0),true))` (+1 more) |
| I6+reread-L578-0coin_p | 27400 | +8 | 2230 | -13 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;((false,Some(args.0),true))` (+1 more) |
| I6+issome-L767-1f1 | 27400 | +8 | 2205 | -38 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;((false,Some(args.0),true))` (+1 more) |
| g_w_clock_local+k_rL | 27400 | +8 | 2235 | -8 | `let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,` -> `let ts=Clock::get()?.unix_timestamp;let e=CollectCreatorFeeEvent{times` (+1 more) |
| g_w_clock_local+ifq-L556-0e | 27400 | +8 | 2236 | -7 | `let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,` -> `let ts=Clock::get()?.unix_timestamp;let e=CollectCreatorFeeEvent{times` (+1 more) |
| g_w_clock_local+iflet-L757-0s | 27400 | +8 | 2235 | -8 | `let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,` -> `let ts=Clock::get()?.unix_timestamp;let e=CollectCreatorFeeEvent{times` (+1 more) |
| wl_ts_clockvar+ifq-L556-0e | 27400 | +8 | 2236 | -7 | `let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,` -> `let clock=Clock::get()?;let e=CollectCreatorFeeEvent{timestamp:clock.u` (+1 more) |
| wl_ts_clockvar+k_rL | 27400 | +8 | 2235 | -8 | `let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,` -> `let clock=Clock::get()?;let e=CollectCreatorFeeEvent{timestamp:clock.u` (+1 more) |
| wl_ts_clockvar+iflet-L757-0s | 27400 | +8 | 2235 | -8 | `let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,` -> `let clock=Clock::get()?;let e=CollectCreatorFeeEvent{timestamp:clock.u` (+1 more) |
| cmpneg-L283-0 | 27392 | +0 | 2243 | +0 | `der=hopt==Some(true);  i` -> `der=!(hopt!=Some(true));  i` |
| cmpneg-L312-0 | 27392 | +0 | 2136 | -107 | `if t==*sharing\|\|t=` -> `if !(t!=*sharing)\|\|t=` |
| X1_I6_nov338 | 27400 | +8 | 2221 | -22 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;((false,Some(args.0),true))` (+1 more) |
| X0_nov338 | 27384 | -8 | 2221 | -22 | `return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}unsafe{core::p` -> `return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}None=>{}}` |
| X2_I6b_nov338 | 27400 | +8 | 2221 | -22 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;(false,Some(args.0),true)` (+1 more) |
| X3_I6c_nov338 | 27352 | -40 | 1579 | -664 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;(false,Some(new),true)` (+1 more) |
| cmpneg-L307-0 | 27392 | +0 | 2243 | +0 | `if t==Pubkey::default(){ret` -> `if !(t!=Pubkey::default()){ret` |
| cmpneg-L338-0 | 27392 | +0 | 2243 | +0 | `if f==0\|\|f>` -> `if !(f!=0)\|\|f>` |
| cmpneg-L312-1 | 27392 | +0 | 2243 | +0 | `t==*holder_key` -> `!(t!=*holder_key)` |
| cmpneg-L339-1 | 27392 | +0 | 2243 | +0 | `a.sharing_config.owner==&FEES` -> `!(a.sharing_config.owner!=&FEES)` |
| cmpneg-L339-0 | 27392 | +0 | 2243 | +0 | `a.sharing_config.key()==a.bonding_curve.creator` -> `!(a.sharing_config.key()!=a.bonding_curve.creator)` |
| cmpneg-L339-3 | 27392 | +0 | 2243 | +0 | `q==anchor_spl::token::spl_token::native_mint::ID` -> `!(q!=anchor_spl::token::spl_token::native_mint::ID)` |
| cmpneg-L339-2 | 27392 | +0 | 2243 | +0 | `q==Pubkey::default()` -> `!(q!=Pubkey::default())` |
| cmpneg-L339-5 | 27392 | +0 | 2243 | +0 | `st.creator!=Pubkey::default()` -> `!(st.creator==Pubkey::default())` |
| cmpneg-L339-4 | 27392 | +0 | 2243 | +0 | `der=hopt==Some(true);let` -> `der=!(hopt!=Some(true));let` |
| cmpswap-L289-0 | 27360 | -32 | 1721 | -522 | `&&!(hopt==Some(true)){re` -> `&&!(Some(true)==hopt){re` |
| cmpswap-L283-0 | 27360 | -32 | 1721 | -522 | `der=hopt==Some(true);  i` -> `der=Some(true)==hopt;  i` |
| cmpswap-L312-0 | 27392 | +0 | 2241 | -2 | `if t==*sharing\|\|t=` -> `if *sharing==t\|\|t=` |
| cmpswap-L307-0 | 27392 | +0 | 2241 | -2 | `if t==Pubkey::default(){ret` -> `if Pubkey::default()==t{ret` |
| cmpswap-L338-0 | 27392 | +0 | 2243 | +0 | `if f==0\|\|f>` -> `if 0==f\|\|f>` |
| cmpswap-L312-1 | 27392 | +0 | 2242 | -1 | `t==*holder_key` -> `*holder_key==t` |
| cmpswap-L339-0 | 27392 | +0 | 2237 | -6 | `a.sharing_config.key()==a.bonding_curve.creator` -> `a.bonding_curve.creator==a.sharing_config.key()` |
| cmpswap-L338-1 | 27392 | +0 | 2243 | +0 | `f>st.max_fee` -> `st.max_fee<f` |
| cmpswap-L339-2 | 27392 | +0 | 2241 | -2 | `q==Pubkey::default()` -> `Pubkey::default()==q` |
| cmpswap-L339-1 | 27392 | +0 | 2242 | -1 | `a.sharing_config.owner==&FEES` -> `&FEES==a.sharing_config.owner` |
| cmpswap-L339-4 | 27360 | -32 | 1721 | -522 | `der=hopt==Some(true);let` -> `der=Some(true)==hopt;let` |
| cmpswap-L339-3 | 27392 | +0 | 2240 | -3 | `q==anchor_spl::token::spl_token::native_mint::ID` -> `anchor_spl::token::spl_token::native_mint::ID==q` |
| ifreq-L284-1e | 27392 | +0 | 2243 | +0 | `if st.mayhem{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin))` -> `if st.mayhem{return err!(PumpError::CtoNotAllowedForMayhemCoin);}` |
| cmpswap-L339-5 | 27392 | +0 | 2241 | -2 | `st.creator!=Pubkey::default()` -> `Pubkey::default()!=st.creator` |
| inline-L339-0 | 27384 | -8 | 1595 | -648 | `let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_` -> `let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards"` |
| inline-L314-0 | 27384 | -8 | 2028 | -215 | `let cashback=if holder{false}else{st.cashback};             match fee{` -> `match fee{Some(f)=>{if st.quote_locked{return Err(error!(PumpError::Cr` |
| inline-L339-2 | 27248 | -144 | 2088 | -155 | `let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default(` -> `let (_holder,cashback,target,sharing_update,collect_old,skip)={ let st` |
| inline-L339-1 | 27392 | +0 | 1866 | -377 | `let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()]` -> `holder_key=(Pubkey::find_program_address(&[b"holder-rewards",mint.as_r` |
| inline-L339-4 | 27360 | -32 | 1601 | -642 | `let args=&(new,);let sk=a.sharing_config.key();let mut target=validate` -> `let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new` |
| inline-L339-3 | compile/none | | | | `let cashback=!holder&&st.cashback;let args=&(new,);let sk=a.sharing_co` -> `let args=&(new,);let sk=a.sharing_config.key();let mut target=validate` |
| issome-L283-0b0 | 27408 | +16 | 1397 | -846 | `der=hopt==Some(true);  i` -> `der=matches!(hopt,Some(true));  i` |
| inline-L339-5 | 27352 | -40 | 2074 | -169 | `let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new` -> `let mut target=validate(&st,hopt,fee,new,&holder_key,&a.sharing_config` |
| issome-L283-2b2 | 27408 | +16 | 1397 | -846 | `der=hopt==Some(true);  i` -> `der=hopt.is_some_and(\|v\|v);  i` |
| issome-L283-1b1 | 27408 | +16 | 1397 | -846 | `der=hopt==Some(true);  i` -> `der=hopt.unwrap_or(false);  i` |
| issome-L283-4b4 | 27408 | +16 | 1397 | -846 | `der=hopt==Some(true);  i` -> `der=(hopt.unwrap_or_default());  i` |
| issome-L283-3b3 | 27360 | -32 | 1721 | -522 | `der=hopt==Some(true);  i` -> `der=(Some(true)==hopt);  i` |
| issome-L289-0b0 | 27248 | -144 | 1688 | -555 | `&&!(hopt==Some(true)){re` -> `&&!(matches!(hopt,Some(true))){re` |
| issome-L289-1b1 | 27248 | -144 | 1688 | -555 | `&&!(hopt==Some(true)){re` -> `&&!(hopt.unwrap_or(false)){re` |

## B2 (13fe453 minus vol334: tie = 27,400 B / M 2,245)

| variant | bytes | dB | M | dM | edit |
| --- | ---: | ---: | ---: | ---: | --- |
| B2_I6 | 27408 | +16 | 2245 | +1 | `let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r` -> `target=a.bonding_curve.creator;((false,Some(args.0),true))` |
| B2_iflet746 | compile/none | | | | `if let Some(val)=sharing_update{     crate::pump_fees::cpi::admin_cto_` -> `match sharing_update{Some(val)=>{     crate::pump_fees::cpi::admin_cto` |
| B2 | 27392 | +0 | 2244 | +0 |  |

Validate-line lattice (autospell on B1, lines 283-339 plus the line-339 entry, w14a73's MIR-identical rows skipped): 42 of
about 80 built before the time box (the rest are in `v2/` of `$OUT`, list `t/w0`/`t/w1`). None is +8 B: the only +8/+16 B
rows lose 300+ M (andand/letswap at L339); everything else is 27,392 B (identical or -1..-7 M) or smaller and worse. `require!`/`err!`/`if`-return, `matches!`/`!=None`,
`&t==sharing`, split/merged compares and `let` placements in validate are MIR-identical or move whole blocks.

## Mechanism summary

- validate's error sites are already the original's shape (`name` + `to_string` calls, line/code immediates), so a +8 B
  change there is either MIR-identical (0 B) or a block-order change (an extra `ja`, -40 M or worse).
- The only +8 B ordinary forms found anywhere (`!x` -> `x==false` at 334/556/559/561, `ifq-L561`, `unwrapor-L757`,
  `iflet-L746`, `ev_cb_local`) all cost 1-48 M against the fill bound, because they move blocks or registers.
- So the line-334 placeholder stays a pure-fill artifact: removing it needs a real +8 B code-shape improvement, not a
  respelling. The best structural +16 B lead is `inline-L339-6` (+1 M on B1 and on B2); it needs an M-neutral -8 B partner.

## Tools (`tools/`, experiment only)

- `capvar.sh`, `capraw2.py`: w14a88/w14a73 capture (IR-only build) + `rx.py` oracle, re-pointed at this lane.
- `runlist.sh` / `drive.sh`: two-worker queue (capvar stdin from /dev/null: without it the first capture eats the list).
- `harvest.sh`: collects rx results of interrupted workers; `rec.py`: ledger rows per variant.
