# w19b22-cto-nat-ctostate-block

Target `0x22a10` `admin_cto::execute`, E2/E3 CtoState block (original offsets 0x420-0x4d0), pinned at 27,400 B.

**Mechanism.** rustc stores an aggregate in field DECLARATION order, not literal order or offset order, and the layout keeps the bools in declaration order after the
32 B and 8 B fields. So `struct CtoState{mayhem,holder_reward,cashback,creator,quote_locked,holder_enabled,fee_configurable,max_fee}` has the same offsets as before and stores
`my hr cb creator ql he fc max_fee`, the original's order. Writing `creator:curve.creator` before the `quote_locked` expression in the literal puts the temp copy in an earlier
block than the aggregate. MemCpyOpt's call-slot rewrite is block-local, so it fails, and the forward leaves `memcpy(st, curve+8)` at the aggregate position. It stays a memcpy (ascending
load/store pairs through one register) as long as `st` is not captured; a volatile read of `st` makes it a memmove (all loads, then all stores).

The ordinary literal is byte-identical to main's `MaybeUninit` field-by-field shim, so this removes that shim.
