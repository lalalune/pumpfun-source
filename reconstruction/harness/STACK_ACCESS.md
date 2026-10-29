# Compare direct stack access layouts

Run `python reconstruction/harness/stack_access.py --original original.so --original-start 0x1000 --original-bytes 0x100 --candidate candidate.so --candidate-start 0x2000 --candidate-bytes 0x108` with actual function ranges. JSON goes to stdout, so redirect to a fresh report path if desired.

Each input receipt includes the binary hash and selected range. Access records retain instruction offsets, signed frame offsets, widths and read/write classification. Differences count accesses by offset, width and direction, exposing moved slots and additional spill/load instructions without treating overlapping ranges as disjoint variables. LDDW continuation words are never decoded as memory instructions.

This is a syntactic comparison, not variable matching, live-range analysis or stack safety verification. Only direct r10-based ordinary memory accesses are classified. Atomic/nonstandard direct operations are listed separately; accesses through aliases to r10 are not resolved. Matching counts do not imply matching order, values or program behavior. No official score is changed.
