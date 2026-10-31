# oracle: grow payload word 1's live segment by 16 empty asm-sideeffect MIs (0 code bytes) in bb68.i, after its load
A='  %_174.1.i = load ptr, ptr %219, align 8, !noalias !8604, !noundef !2\n'
EDITS=[(A,A+'  call void asm sideeffect "", ""()\n'*16)]
