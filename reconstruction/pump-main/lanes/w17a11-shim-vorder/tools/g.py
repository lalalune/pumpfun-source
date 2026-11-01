# w17a11 shim genes: (file, old, new) exact single-occurrence replacements; line counts must not change.
G={}
L326='match fee{Some(f)=>{if st.quote_locked{'
L338E='read_volatile(holder_key as *const Pubkey as *const u8)};}None=>{}}'
def FEE(p):
    return [('cto',L326,'if unsafe{expect_p(fee.is_some(),true,%s)}/*shim: fee Some %s (spill-slot sort)*/{let f=unsafe{*(&fee as *const Option<u64> as *const u64).add(1)}/*shim: fee payload read, no tag re-test*/;if st.quote_locked{'%(p,p)),
            ('cto',L338E,'read_volatile(holder_key as *const Pubkey as *const u8)};}')]
G['fee50']=FEE('0.5')
G['fee47']=FEE('0.47')
# match kept, only the discriminant hinted through a separate is_some test before the match is not possible; alt: if let
def FEEL(p):
    return [('cto',L326,'if let Some(f)=fee{if unsafe{expect_p(true,true,%s)}{}/*shim*/if st.quote_locked{'%p),('cto',L338E,'read_volatile(holder_key as *const Pubkey as *const u8)};}')]
