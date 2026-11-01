# w19a08-shim-nat-xcopy: the sharing tree in plain Rust (peel)

Target `0x22a10` `admin_cto::execute`. Full notes and tools: `origin/swarm/w19a08-shim-nat-xcopy`.

The Some(None) copy at 0x1140-0x1178 is now plain Rust, with no shim on it:

    's:{let x:Option<Pubkey>;if holder{x=None;sharing_update=Some(x);break 's;}x=new;sharing_update=Some(x);}(false,!holder)

- x is assigned twice, so MIR keeps its storage markers and SROA cuts it into the original's 7 B and 9 B pieces, hosted at -0x450 and -0x2d0.
- Its lifetime.start sits in the threaded heads (0xe38, 0x1128, 0x1830), so MemCpyOpt sees a MemoryPhi over two lifetime.start calls and keeps the uninit copy.
- The labelled block puts StorageDead(x) in each arm. Lifetime markers of allocas are never sunk, so SimplifyCFG leaves the two copies in their arms.
- `(false,!holder)` keeps skip non-constant at the join, so the phi is not inverted and r3 keeps the original's polarity.
