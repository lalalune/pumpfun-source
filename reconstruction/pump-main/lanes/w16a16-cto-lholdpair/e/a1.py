# (a') cashback select reads st.cashback back from the stack copy after the stores (deeper DAG dependency)
EDITS=[("  %extract.t = icmp ne i8 %i28, 0\n","  %cbr = load i8, ptr %i40, align 2\n  %extract.t = icmp ne i8 %cbr, 0\n")]
