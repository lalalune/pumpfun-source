# Lane w6r1-execute-ir-admincto: 0x22a10 `admin_cto::execute` (IR-oracle loop)

Lane name note: the wave-6 lane `w6r1-execute-ir` was assigned to two agents (sweep::execute 0x72810 and
admin_cto::execute 0x22a10). This agent works on 0x22a10 under the suffixed name `w6r1-execute-ir-admincto`
(worktree, branch, OUT dir and ledger lane) so the two do not collide.

Base: origin/main 099b0dd (programs/ identical on cebf6bbb): 1027/1035 normalized, 276 raw.
Target on base: 27,416 B (orig 27,400), ratio 0.36328, calls 154/3 (= orig).

## Trials

| trial | mechanism | bytes | ratio | official | ledger |
|---|---|---:|---:|---|---|
| base | origin/main | 27,416 | 0.36328 | 1027/276 | |
| t1 (w4 repro) | holder sweep closure -> nested `fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)` | 27,424 | 0.36952 | (w4: raw loss 0xa868) | w4 |
| b | wallet (collect_old) closure -> nested `fn wallet(ctx:&Context<AdminCto>)` | 27,336 | 0.36953 | not scored | 17d3f8a8 |
| **ab** | both | **27,344** | **0.37637** | **1027/276, zero losses (raw 0xa868 kept)** | 94a22994 |

## Mechanism

Both closures captured `a=&ctx.accounts` through a closure environment; inlined, the env pointer is
`noalias`-scoped, so LLVM keeps fewer field reloads after calls. The original reloads account fields
(for example `holder_creator_vault.key` at r8+0x108 after the 648 error!) as code that takes `&Context`
would. Two nested fns taking `&Context<AdminCto>` reproduce that in both regions, and the size deltas
(+8 and -80 B) cancel enough that no raw membership moves.
