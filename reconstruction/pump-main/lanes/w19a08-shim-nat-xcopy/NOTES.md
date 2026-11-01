# w19a08-shim-nat-xcopy: the original's blocks around Some(None)

Target `0x22a10` `admin_cto::execute`. Full notes, genes and IR tools: `origin/swarm/w19a08-shim-nat-xcopy`.

- `let ns=!shared;` with every shared test in validate on `ns`: rustc creates the creator arm's block first and MIR JumpThreading still threads, so the shared test is `jeq shared,0` as at 0xdc0. No shim.
- The None temp is declared in the shared arm's head, before the holder test, so its lifetime.start sits in the threaded heads. Those heads are the original's blocks 0xe38, 0x1128 and 0x1830: they hold only markers at IR level, and PHI copies land in them. The None block has two predecessors and no lifetime.start of its own, so its 7 B copy lowers high word first, as at 0x1140.
- `llvm.var.annotation` after the copy stops SimplifyCFG sinking the two arms' copies into a pointer phi.
- #4177's two clone trap weights come out here: on this structure they lower C1. One error-path byte read repays the last 8 B.
