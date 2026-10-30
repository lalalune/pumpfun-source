import runpy
EDITS=runpy.run_path('e/T1.py')['EDITS']+[("let holder_key;let hk=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID);holder_key=hk.0;","let holder_key;holder_key=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID).0;")]
