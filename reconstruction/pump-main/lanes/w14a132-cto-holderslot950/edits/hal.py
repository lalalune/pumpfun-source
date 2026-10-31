# per-arm holder constant stored to one alloca at validate's arm exits
import os
W=os.environ.get('HW','i8')
EDITS=[
("start:\n","start:\n  %hslot = alloca "+W+", align "+('1' if W=='i8' else '8')+"\n"),
("bb45.i:                                           ; preds = %bb38.i\n","bb45.i:                                           ; preds = %bb38.i\n  store "+W+" 0, ptr %hslot\n"),
("bb44.i:                                           ; preds = %bb22.i\n","bb44.i:                                           ; preds = %bb22.i\n  store "+W+" 1, ptr %hslot\n"),
("bb52.i:                                           ; preds = %bb47.i\n","bb52.i:                                           ; preds = %bb47.i\n  store "+W+" 0, ptr %hslot\n"),
("bb95.i:                                           ; preds = %bb44.i\n","bb95.i:                                           ; preds = %bb44.i\n  store "+W+" 1, ptr %hslot\n"),
]
