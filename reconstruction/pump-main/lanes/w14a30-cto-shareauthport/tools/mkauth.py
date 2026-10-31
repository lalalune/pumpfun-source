# mkauth.py <order like key.rent.f41.f40.owner.f42> <outfile.py>: source edit for the sharing authority literal read order
import sys
m={'key':'key:x.key','rent':'rent_epoch:x.rent_epoch','owner':'owner:x.owner','f40':'is_signer:x.is_signer','f41':'is_writable:x.is_writable','f42':'executable:x.executable'}
old="AccountInfo{rent_epoch:x.rent_epoch,owner:x.owner,lamports:lamports,key:x.key,is_writable:x.is_writable,is_signer:x.is_signer,executable:x.executable,data:data}"
new="AccountInfo{"+",".join(m[k] for k in sys.argv[1].split('.'))+",lamports:lamports,data:data}"
open(sys.argv[2],'w').write('EDITS=[(%r,%r)]\n'%(old,new))
