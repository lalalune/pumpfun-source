"""Mutation set 2: hand-written structural respellings + generated families.

Generated families (all within swap_hop, all line-preserving):
  qm-<n>   : `expr?` -> `match expr { Ok(v) => v, Err(e) => return Err(e) }`   (? vs explicit match)
  qmm-<n>  : `expr?` -> `expr.map_err(|e| e)?`                                 (? vs map_err)
  key-<n>  : `&<path>.key()` argument -> temp bound in a `let` at statement start (binding split)
Hand-written: whitelist / complete_fill structure, accrual, completion event.
"""
import re
from pathlib import Path
import mutations as base

SRC = Path(__file__).resolve().parents[4] / "programs/pump/src/multi_hop_curve_swap.rs"
M = list(base.M)


def m(mid, old, new):
    assert old.count("\n") == new.count("\n"), mid
    M.append((mid, old, new))


# ---- whitelist / complete_fill ---------------------------------------------------------
W = "{ let user = a.user.key(); require!(!c.is_mayhem_mode && user!=a.global.whitelist_pda,PumpError::NotEnoughTokensToBuy); }"
m("wl-two-requires", W,
  "require!(!c.is_mayhem_mode,PumpError::NotEnoughTokensToBuy); { let user = a.user.key(); require!(user!=a.global.whitelist_pda,PumpError::NotEnoughTokensToBuy); }")
m("wl-two-ifs", W,
  "if c.is_mayhem_mode { return err!(PumpError::NotEnoughTokensToBuy); } { let user = a.user.key(); if user==a.global.whitelist_pda { return err!(PumpError::NotEnoughTokensToBuy); } }")
m("wl-else-if", W,
  "{ let user = a.user.key(); if c.is_mayhem_mode { return err!(PumpError::NotEnoughTokensToBuy); } else if user==a.global.whitelist_pda { return err!(PumpError::NotEnoughTokensToBuy); } }")
m("wl-user-ref", W,
  "{ let user = &a.user.key(); require!(!c.is_mayhem_mode && *user!=a.global.whitelist_pda,PumpError::NotEnoughTokensToBuy); }")
m("wl-ne-method", W,
  "{ let user = a.user.key(); require!(!c.is_mayhem_mode && user.ne(&a.global.whitelist_pda),PumpError::NotEnoughTokensToBuy); }")
m("wl-wl-lhs", W,
  "{ let user = a.user.key(); require!(!c.is_mayhem_mode && a.global.whitelist_pda!=user,PumpError::NotEnoughTokensToBuy); }")
m("wl-keys-neq", W,
  "{ let user = a.user.key(); require_keys_neq!(user,a.global.whitelist_pda,PumpError::NotEnoughTokensToBuy); }")
M.pop()  # require_keys_neq logs both keys: behaviour change
m("wl-matches", W,
  "{ let user = a.user.key(); require!(!(c.is_mayhem_mode || user==a.global.whitelist_pda),PumpError::NotEnoughTokensToBuy); }")
m("wl-user-copy-bytes", W,
  "{ let user = a.user.key().to_bytes(); require!(!c.is_mayhem_mode && user!=a.global.whitelist_pda.to_bytes(),PumpError::NotEnoughTokensToBuy); }")
m("wl-global-bind", W,
  "{ let user = a.user.key(); let wl = a.global.whitelist_pda; require!(!c.is_mayhem_mode && user!=wl,PumpError::NotEnoughTokensToBuy); }")

CF = ("                if let Some((fees, quote, post)) = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,\n"
      "                    &h.associated_base_bonding_curve,flag,p_rate,c_rate,trade_amount)? {\n"
      "                    post_fill=Some(post);\n"
      "                    (reserves,quote,fees.protocol_fee,fees.creator_fee,post.base_out)\n"
      "                }else{post_fill=None;(reserves,q,pf,cf,0)}")
m("cf-bind-result", CF,
  "                let filled = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,\n"
  "                    &h.associated_base_bonding_curve,flag,p_rate,c_rate,trade_amount)?; if let Some((fees, quote, post)) = filled {\n"
  "                    post_fill=Some(post);\n"
  "                    (reserves,quote,fees.protocol_fee,fees.creator_fee,post.base_out)\n"
  "                }else{post_fill=None;(reserves,q,pf,cf,0)}")
m("cf-tuple-before-assign", CF,
  "                if let Some((fees, quote, post)) = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,\n"
  "                    &h.associated_base_bonding_curve,flag,p_rate,c_rate,trade_amount)? {\n"
  "                    let r = (reserves,quote,fees.protocol_fee,fees.creator_fee,post.base_out); post_fill=Some(post);\n"
  "                    r\n"
  "                }else{post_fill=None;(reserves,q,pf,cf,0)}")
m("cf-map-or", CF,
  "                let filled = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,\n"
  "                    &h.associated_base_bonding_curve,flag,p_rate,c_rate,trade_amount)?; post_fill = filled.map(|(_,_,post)| post);\n"
  "                    match filled { Some((fees, quote, post)) =>\n"
  "                    (reserves,quote,fees.protocol_fee,fees.creator_fee,post.base_out),\n"
  "                None=>(reserves,q,pf,cf,0)}")
m("cf-none-first", CF,
  "                match complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,\n"
  "                    &h.associated_base_bonding_curve,flag,p_rate,c_rate,trade_amount)? { None=>{post_fill=None;(reserves,q,pf,cf,0)}\n"
  "                    Some((fees, quote, post))=>{post_fill=Some(post);\n"
  "                    (reserves,quote,fees.protocol_fee,fees.creator_fee,post.base_out)\n"
  "                }}")

# ---- accrual / buyback ----------------------------------------------------------------
PB = ("        let post_buyback_raw = if let Some(post)=post_fill.as_ref() {\n"
      "            h.bonding_curve.post_complete_base_out=post.base_out;\n"
      "            h.bonding_curve.post_complete_quote_in=post.quote_in;\n"
      "            h.bonding_curve.accrue_fees(&a.global,post.fees.protocol_fee,post.fees.creator_fee)?\n"
      "        }else{0};")
m("pb-match", PB,
  "        let post_buyback_raw = match post_fill.as_ref() { Some(post) => {\n"
  "            h.bonding_curve.post_complete_base_out=post.base_out;\n"
  "            h.bonding_curve.post_complete_quote_in=post.quote_in;\n"
  "            h.bonding_curve.accrue_fees(&a.global,post.fees.protocol_fee,post.fees.creator_fee)?\n"
  "        } None => 0 };")
m("pb-none-first", PB,
  "        let post_buyback_raw = match post_fill.as_ref() { None => 0, Some(post) => {\n"
  "            h.bonding_curve.post_complete_base_out=post.base_out;\n"
  "            h.bonding_curve.post_complete_quote_in=post.quote_in;\n"
  "            h.bonding_curve.accrue_fees(&a.global,post.fees.protocol_fee,post.fees.creator_fee)?\n"
  "        } };")
m("pb-copy", PB,
  "        let post_buyback_raw = if let Some(post)=post_fill {\n"
  "            h.bonding_curve.post_complete_base_out=post.base_out;\n"
  "            h.bonding_curve.post_complete_quote_in=post.quote_in;\n"
  "            h.bonding_curve.accrue_fees(&a.global,post.fees.protocol_fee,post.fees.creator_fee)?\n"
  "        }else{0};")
m("pb-is-some", PB,
  "        let post_buyback_raw = if post_fill.is_some() { let post = post_fill.as_ref().unwrap();\n"
  "            h.bonding_curve.post_complete_base_out=post.base_out;\n"
  "            h.bonding_curve.post_complete_quote_in=post.quote_in;\n"
  "            h.bonding_curve.accrue_fees(&a.global,post.fees.protocol_fee,post.fees.creator_fee)?\n"
  "        }else{0};")
M.pop()  # adds an unwrap panic edge
m("pb-curve-bind", PB,
  "        let post_buyback_raw = if let Some(post)=post_fill.as_ref() { let curve = &mut h.bonding_curve;\n"
  "            curve.post_complete_base_out=post.base_out;\n"
  "            curve.post_complete_quote_in=post.quote_in;\n"
  "            curve.accrue_fees(&a.global,post.fees.protocol_fee,post.fees.creator_fee)?\n"
  "        }else{0};")
m("accrue-curve-bind",
  "let buyback_raw = h.bonding_curve.accrue_fees(&a.global,fees.protocol_fee,fees.creator_fee)?;",
  "let buyback_raw = { let curve = &mut h.bonding_curve; curve.accrue_fees(&a.global,fees.protocol_fee,fees.creator_fee)? };")
m("accrue-fees-fields-bound",
  "let buyback_raw = h.bonding_curve.accrue_fees(&a.global,fees.protocol_fee,fees.creator_fee)?;",
  "let (protocol_fee,creator_fee) = (fees.protocol_fee,fees.creator_fee); let buyback_raw = h.bonding_curve.accrue_fees(&a.global,protocol_fee,creator_fee)?;")
m("buyback-flag-bool",
  "        if flag & 1 != 0 {\n            if native {",
  "        if (flag & 1) != 0 {\n            if native {")
M.pop()  # parenthesization only: identical tokens after parse
m("buyback-nested-match",
  "            if native {\n                native_buyback(a,event_bump,&h.bonding_curve,paid_buyback)?;\n            } else if paid_buyback != 0 {",
  "            if native {\n                native_buyback(a,event_bump,&h.bonding_curve,paid_buyback)?;\n            } else if paid_buyback > 0 {")

# ---- completion / post event ----------------------------------------------------------
m("post-event-match",
  "        if let Some(post)=post_fill {",
  "        if let Some(ref post)=post_fill {")
m("completion-curve-key-first",
  "            let completion=crate::trade_types::CompleteEvent { mint:h.base_mint.key(),user:a.user.key(),\n                bonding_curve:h.bonding_curve.key(),timestamp,quote_mint:h.bonding_curve.quote_mint };",
  "            let curve_key = h.bonding_curve.key(); let completion=crate::trade_types::CompleteEvent { mint:h.base_mint.key(),user:a.user.key(),\n                bonding_curve:curve_key,timestamp,quote_mint:h.bonding_curve.quote_mint };")
m("completion-reuse-curve-key",
  "                bonding_curve:h.bonding_curve.key(),timestamp,quote_mint:h.bonding_curve.quote_mint };",
  "                bonding_curve:curve_key,timestamp,quote_mint:h.bonding_curve.quote_mint };")
m("complete-flag-after-event",
  "if completed { h.bonding_curve.complete=true;\n            let completion=crate::trade_types::CompleteEvent { mint:h.base_mint.key(),user:a.user.key(),\n                bonding_curve:h.bonding_curve.key(),timestamp,quote_mint:h.bonding_curve.quote_mint };",
  "if completed {\n            let completion=crate::trade_types::CompleteEvent { mint:h.base_mint.key(),user:a.user.key(),\n                bonding_curve:h.bonding_curve.key(),timestamp,quote_mint:h.bonding_curve.quote_mint }; h.bonding_curve.complete=true;")

# ---- prologue -------------------------------------------------------------------------
m("vt-from",
  "crate::trade::validate_trade(h.bonding_curve.complete as u8,h.bonding_curve.is_cashback_coin as u64,(flag & 2 == 0) as u64)?;",
  "crate::trade::validate_trade(u8::from(h.bonding_curve.complete),u64::from(h.bonding_curve.is_cashback_coin),u64::from(flag & 2 == 0))?;")
m("vt-curve-bind",
  "crate::trade::validate_trade(h.bonding_curve.complete as u8,h.bonding_curve.is_cashback_coin as u64,(flag & 2 == 0) as u64)?;",
  "let curve = &h.bonding_curve; crate::trade::validate_trade(curve.complete as u8,curve.is_cashback_coin as u64,(flag & 2 == 0) as u64)?;")
m("vt-no-creator-bind",
  "crate::trade::validate_trade(h.bonding_curve.complete as u8,h.bonding_curve.is_cashback_coin as u64,(flag & 2 == 0) as u64)?;",
  "let no_creator = (flag & 2 == 0) as u64; crate::trade::validate_trade(h.bonding_curve.complete as u8,h.bonding_curve.is_cashback_coin as u64,no_creator)?;")
m("vt-flag-ne",
  "(flag & 2 == 0) as u64)?;",
  "!(flag & 2 != 0) as u64)?;")
m("prepare-reborrow",
  "        prepare_curve(a,h)?;",
  "        prepare_curve(&*a,&*h)?;")
M.pop()  # same MIR
m("mayhem-if-return",
  "require!(!h.bonding_curve.is_mayhem_mode,PumpError::MultiHopMayhemCurveNotSupported);",
  "if h.bonding_curve.is_mayhem_mode { return err!(PumpError::MultiHopMayhemCurveNotSupported); }")


# ---- generated families -----------------------------------------------------------------
def _fn_range(t):
    s = t.index("fn swap_hop<'info>")
    e = t.index("pub use crate::payments::mhc_transfer_quote_out", s)
    return s, e


IDENT = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_:.<>")


def _expr_start(t, close):
    """close = index of ')' just before '?'. Return start of the call-chain expression."""
    i = close
    while True:
        if t[i] == ")":
            d = 0
            while True:
                if t[i] == ")": d += 1
                elif t[i] == "(": d -= 1
                if d == 0: break
                i -= 1
            i -= 1
            while i >= 0 and t[i] in IDENT:
                i -= 1
            if t[i] == ")":
                continue
            return i + 1
        return i + 1


def _unique(t, a, b, lo, hi):
    """extend [a,b) right until unique in t (within one line)."""
    while t.count(t[a:b]) != 1 and b < hi and t[b] != "\n":
        b += 1
    while t.count(t[a:b]) != 1 and a > lo and t[a - 1] != "\n":
        a -= 1
    return (a, b) if t.count(t[a:b]) == 1 else None


def _gen():
    t = SRC.read_text()
    s, e = _fn_range(t)
    n = 0
    for mo in re.finditer(r"\)\?", t[s:e]):
        q = s + mo.start() + 1           # index of '?'
        st = _expr_start(t, q - 1)
        expr = t[st:q]
        if "\n" in expr or not re.match(r"[A-Za-z&*]", expr):
            continue
        u = _unique(t, st, q + 1, s, e)
        if not u:
            continue
        a, b = u
        old = t[a:b]
        pre, post = t[a:st], t[q + 1:b]
        n += 1
        tag = re.sub(r"[^a-z0-9]+", "-", expr.split("(")[0].split("::")[-1].lower()).strip("-")[:24]
        m(f"qm-{n:02d}-{tag}", old, pre + f"match {expr} {{ Ok(v) => v, Err(e) => return Err(e) }}" + post)
        m(f"qmm-{n:02d}-{tag}", old, pre + f"{expr}.map_err(|e| e)?" + post)
    k = 0
    seen = set()
    for mo in re.finditer(r"&((?:a|h)\.[a-z_]+)\.key\(\)", t[s:e]):
        p0 = s + mo.start()
        path = mo.group(1)
        # statement start: previous ';' or '{' or '}' on the same line
        ls = t.rfind("\n", 0, p0) + 1
        cands = [t.rfind(ch, ls, p0) for ch in ";{}"]
        ss = max(cands)
        if ss < 0:
            ss = ls + (len(t[ls:p0]) - len(t[ls:p0].lstrip()))
        else:
            ss += 1
        stmt_head = t[ss:p0]
        u = _unique(t, ss, p0 + len(mo.group(0)), s, e)
        if not u:
            continue
        a, b = u
        if a != ss:
            continue
        old = t[a:b]
        k += 1
        var = f"k{k}"
        new = f" let {var} = {path}.key();" + stmt_head + "&" + var + t[p0 + len(mo.group(0)):b]
        if old in seen:
            continue
        seen.add(old)
        m(f"key-{k:02d}-{path.split('.')[1][:20]}", old, new)


_gen()

if __name__ == "__main__":
    t = SRC.read_text()
    for mid, o, n in M:
        c = t.count(o)
        if c != 1 or mid.startswith(("qm-", "key-")):
            print(mid, c, "|", o[:90].replace("\n", "\\n"), "=>", n[:120].replace("\n", "\\n"))
    print(len(M))
