# oracle: payload word 1 (Err-return ptr phi, MIR %1659) hinted to r9 by an empty inline-asm {r9} use in the return block
EDITS=[("  %766 = insertvalue { i64, ptr } %765, ptr %_0.sroa.11.1, 1\n","  call void asm sideeffect \"\", \"{r9}\"(ptr %_0.sroa.11.1)\n  %766 = insertvalue { i64, ptr } %765, ptr %_0.sroa.11.1, 1\n")]
