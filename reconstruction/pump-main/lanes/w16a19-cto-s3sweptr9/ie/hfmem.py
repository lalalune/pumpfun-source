# IR oracle (shim emulation): S3's per-arm holder flag through a volatile stack slot: write_volatile at the validate Ok
# merge (bb75, after its phis), read_volatile at the curve store (bb37). HFW=i8|i64 picks the slot width.
import os
W=os.environ.get('HFW','i8')
P3="  %target.i.sroa.8.0 = phi ptr [ %target.i.sroa.8.0.copyload289, %bb45.i ], [ %target.i.sroa.8.1, %bb65.i ], [ %target.i.sroa.8.0.copyload, %bb44.i ]\n"
ST=("  store volatile i8 %hf.sroa.0.0, ptr %hfm, align 8\n" if W=='i8' else "  %hfz = zext i8 %hf.sroa.0.0 to i64\n  store volatile i64 %hfz, ptr %hfm, align 8\n")
LD=("  %hfl = load volatile i8, ptr %hfm, align 8\n" if W=='i8' else "  %hfl8 = load volatile i64, ptr %hfm, align 8\n  %hfl = trunc i64 %hfl8 to i8\n")
EDITS=[
 ("  %_267 = alloca [1 x i8], align 1\n","  %_267 = alloca [1 x i8], align 1\n  %hfm = alloca [8 x i8], align 8\n"),
 (P3,P3+ST),
 ("  store i8 %hf.sroa.0.0, ptr %582, align 1\n",LD+"  store i8 %hfl, ptr %582, align 1\n"),
]
