EDITS=[('let hopt=holder;let holder=hopt==Some(true);', 'let hopt=holder;let holder=if let Some(h)=hopt{h}else{false};')]
