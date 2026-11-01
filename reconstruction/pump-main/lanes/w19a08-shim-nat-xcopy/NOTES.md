# w19a08-shim-nat-xcopy: Some(None) is a plain None local (peel)

Target `0x22a10` `admin_cto::execute`. Full notes and tools: `origin/swarm/w19a08-shim-nat-xcopy`.

`let x:Option<Pubkey>;` in the shared arm's head, `x=None;sharing_update=Some(x)` on the holder arm, `x=new;sharing_update=Some(x)` otherwise. x is assigned twice, so MIR keeps its storage markers and SROA cuts it into the 7 B and 9 B pieces. Its lifetime.start then sits in the threaded heads, so the None block's source clobber is a MemoryPhi over two lifetime.start calls and MemCpyOpt keeps the uninit copy. No MaybeUninit, raw copy or passthrough is needed. One zero-instruction annotation remains on the holder arm: it stops SimplifyCFG sinking the two copies into a pointer phi.
