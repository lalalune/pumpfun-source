import runpy
EDITS=[]
EDITS+=runpy.run_path('edits/v1.py')['EDITS']
EDITS+=[('let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;','let holder_key=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID).0;')]
