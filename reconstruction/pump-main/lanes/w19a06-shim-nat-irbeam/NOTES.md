# w19a06-shim-nat-irbeam

Target `0x22a10` `admin_cto::execute`. Tools and tables are on `origin/swarm/w19a06-shim-nat-irbeam`.

This landing, on main e59b48eb1 (0.81611): w19a07's `dk` form of the sweep `dest` (the `dest` value in a `MaybeUninit` of the `then` closure), Rc overflow-trap weights of 1:20 on the C1 clones of mint, sharing_config, event_authority and program (plain `rl20`/`rd20` helpers, so the trap blocks keep the IR order of `Rc::clone`; a macro or `#[inline(always)]` body flips the block placement), and the pin fill moved from the holder_enabled test to the head of the holder_reward test.
