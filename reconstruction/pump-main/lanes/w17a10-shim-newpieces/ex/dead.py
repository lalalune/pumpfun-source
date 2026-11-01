B15='  call void @llvm.memcpy.p0.p0.i64(ptr align 1 %_45, ptr align 1 %new, i64 33, i1 false)\n'
V={
 'dead_vl_new0':[(B15,B15+'  %dz = load volatile i8, ptr %new, align 1\n')],
 'dead_vl_45':[(B15,B15+'  %dz = load volatile i8, ptr %_45, align 1\n')],
 'dead_vl_new8':[(B15,B15+'  %dz.p = getelementptr inbounds i8, ptr %new, i64 8\n  %dz = load volatile i64, ptr %dz.p, align 1\n')],
 'dead_vl_new32':[(B15,B15+'  %dz.p = getelementptr inbounds i8, ptr %new, i64 32\n  %dz = load volatile i8, ptr %dz.p, align 1\n')],
 'dead_fence':[(B15,B15+'  call void asm sideeffect "", "~{memory}"()\n')],
}
