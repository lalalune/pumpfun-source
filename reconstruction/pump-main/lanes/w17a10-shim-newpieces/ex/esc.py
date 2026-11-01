exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces/ex/c1.py').read())
B15='  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_45, ptr align 1 %new, i64 33, i1 false)\n'
ESC=B15+'  call void asm sideeffect "", "r,~{memory}"(ptr %new)\n'
ESC45=B15+'  call void asm sideeffect "", "r,~{memory}"(ptr %_45)\n'
VCALL='i64 %106, ptr noalias nocapture noundef readonly align 1 dereferenceable(33) %new, ptr noalias noundef readonly align 1 dereferenceable(32) %holder_key'
C1A=(VAL,piece('%sharing_update16','%val8'))
V={
 'esc_main':[(B15,ESC)],
 'esc_c1a':[(B15,ESC),C1A],
 'esc45_c1a':[(B15,ESC45),C1A],
 'fa_c1a':[(VCALL,VCALL.replace('%new,','%_45,')),C1A],
 'fa_esc_c1a':[(VCALL,VCALL.replace('%new,','%_45,')),(B15,ESC),C1A],
 'fa_main':[(VCALL,VCALL.replace('%new,','%_45,'))],
}
