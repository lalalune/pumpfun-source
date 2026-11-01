# early curve store: is_holder_reward written with the closure's masked holder right after its def; the late store removed
import os
EDITS=[('  %_0.sroa.0.0.off0.i.not.i = icmp eq i8 %46, 0\n','  %_0.sroa.0.0.off0.i.not.i = icmp eq i8 %46, 0\n  %cb_e = load ptr, ptr %6, align 8, !nonnull !2, !align !3, !noundef !2\n  %cb_h = getelementptr inbounds i8, ptr %cb_e, i64 165\n  store '+os.environ.get('ES_VOL','')+'i8 %46, ptr %cb_h, align 1\n'),
       ('  store i8 %46, ptr %675, align 1\n','')]
