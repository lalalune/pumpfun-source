# Lane w7r1-v3buycosts-anchor: `trade::v3_buy_costs` (original 0x80df8, 2,120 B)

Angle: Anchor and account-access shape (how account-derived values reach the function).
Base: origin/main 34487f839 (1027 normalized / 276 raw, unstripped sha256 ec660de7...).
Target unchanged: 2,136 B, ratio 0.920, 17/17 calls. **No source change is proposed.**

## Result: the angle cannot reach this function

`v3_buy_costs` takes no accounts. Account data reaches it only as eight scalar or pointer
arguments, and the original fixes that ABI exactly: r1 sret, r2 `buyback_bps`, r3 a
non-extended u8 (`and64 r3, 0xff`), r4 the `quote_fee` pointer, and four stack arguments
(`quote`, `protocol_fee`, `creator_fee`, `post` as a nullable pointer). Our signature
already produces the same prologue loads.

So caller and account shape can only reach the body through:

1. parameter and function attributes derived from the types (noalias, readonly, align,
   dereferenceable sizes, sret flags, extension). On the one-function llc oracle, 8 of 9
   attribute variants give the same listing as the base (2,136 B, -9/+11). `zeroext` on
   `is_mayhem` drops the mask, and the original keeps it;
2. linkage or calling convention: switching from internal fastcc to external C gives the
   same listing;
3. IPO from the callers: IPSCCP constant arguments or function specialization. There are 0
   `.specialized` clones in the module, every argument is used, and the function is
   `inline(never)`. The callee is optimized bottom-up from its own body, so callers cannot
   change its IR;
4. how the arguments are spelled at the call sites (`u8::from`, `Some(&*post)`, explicit
   match instead of `.as_ref()`): the full build gives a byte-identical ELF.

A `bool` parameter (which would remove the zero heuristic on the mayhem branch) gives
2,088 B with a -35/+31 diff on the oracle, and it contradicts the original's u8 mask.

This agrees with the w4-v3costs and w7r1-v3buycosts-frame findings. The residual is the
sret register-allocation tie, and it depends only on the MBFI frequencies of the 375
`to_string` panic block and the first split's try_from panic block. Only a `!prof` on
`%43` closes it, and no account-side shape changes those blocks.

## Ledger rows

* 0x80df8-main-34487f8-param-attr-ipo-oracle-v1 (analyzed)
* 0x80df8-main-34487f8-callsite-arg-spelling-v1 (rejected, byte-identical ELF)
* 0x80df8-main-34487f8-param-attr-matrix-oracle-v1 (analyzed)
* 0x80df8-main-34487f8-mayhem-bool-param-oracle-v1 (rejected)

Oracle: the w7r1-v3buycosts-frame `irexp.py`/`one.ll`, copied to
`~/.cache/pumpfun-reconstruction/lanes/w7r1-v3buycosts-anchor/{bin,ed,irexp}`.
