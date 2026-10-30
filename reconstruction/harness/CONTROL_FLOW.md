# Control-flow inspection

Inspect an original or candidate function without an installed SDK:

```sh
python3 reconstruction/harness/control_flow.py reconstruction/base/original.so --start 0x14f4e0 --size 13224 --json /tmp/buy-flow.json
```

The report binds the graph to the binary SHA-256. Block, edge and call-site offsets
are relative to the selected function; direct-call targets are absolute addresses.
It distinguishes conditional/unconditional branches, exits, calls and unreachable
blocks. LDDW continuation slots are never decoded as instructions. Branches into
those slots produce diagnostics and exit status 1; malformed inputs exit 2.

External edges and call immediates are descriptive. Relocations are not resolved,
indirect callees are unknown, and an external edge is not automatically invalid.
Use this to compare control-flow shape and locate reconstruction work, not to
establish runtime equivalence or replace the official scorer.
