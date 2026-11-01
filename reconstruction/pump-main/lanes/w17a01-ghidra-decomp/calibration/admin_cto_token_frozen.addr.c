              
              void pump_recovered::admin_cto::token_frozen(longlong *param_1,undefined8 param_2)
              
              {
                longlong lVar1;
                longlong lStack_d0;
                longlong lStack_c8;
                longlong lStack_c0;
                undefined8 *puStack_b8;
                longlong *plStack_b0;
                char cStack_54;
                int iStack_38;
                undefined8 uStack_10;
                undefined8 uStack_8;
                
/*   18-   18*/  lVar1 = solana_account_info::AccountInfo::data_is_empty(param_2);
/*   20-   20*/  if (lVar1 == 0) {
/*   30-   40*/    solana_account_info::AccountInfo::try_borrow_data(&lStack_c0,param_2);
/*   70-   70*/    if (lStack_c0 == -0x7fffffffffffffe6) {
/*   80-   80*/      uStack_10 = *puStack_b8;
/*   88-   88*/      uStack_8 = puStack_b8[1];
/*   c0-   c0*/      <anchor_spl::token_interface::TokenAccount_as_anchor_lang::AccountDeserialize>::try_deserialize_unchecked
/*   a8-   c0*/                (&lStack_c0,&uStack_10);
/*   d0-   d0*/      if (iStack_38 == 2) {
/*   f0-   f0*/        param_1[1] = (longlong)puStack_b8;
/*   f8-   f8*/        *param_1 = lStack_c0;
                    }
                    else {
/*  198-  1a8*/        *(bool *)(param_1 + 1) = cStack_54 == '\x02';
/*  1b0-  1b0*/        *param_1 = 2;
                    }
/*  1b8-  1c8*/      *plStack_b0 = *plStack_b0 + -1;
                  }
                  else {
/*  158-  158*/      <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/*  140-  158*/                (&lStack_d0,&lStack_c0);
/*  170-  170*/      param_1[1] = lStack_c8;
/*  178-  178*/      *param_1 = lStack_d0;
                  }
                }
                else {
/*  108-  108*/    *param_1 = 2;
/*  110-  110*/    *(undefined1 *)(param_1 + 1) = 0;
                }
/*  1d0-  1d0*/  return;
              }
              
