              
              void pump_recovered::__private::__global::migrate_bonding_curve_creator
                             (longlong *param_1,longlong param_2,undefined8 param_3,undefined8 param_4)
              
              {
                longlong lVar1;
                longlong lVar2;
                longlong lVar3;
                longlong lStack_428;
                longlong lStack_420;
                longlong lStack_418;
                undefined8 uStack_410;
                longlong lStack_408;
                longlong lStack_400;
                undefined2 uStack_3f3;
                undefined1 uStack_3f1;
                undefined8 uStack_3f0;
                undefined8 uStack_3e8;
                longlong lStack_3e0;
                longlong lStack_3d8;
                longlong lStack_3d0;
                undefined1 auStack_3c8 [216];
                longlong *plStack_2f0;
                longlong *plStack_2e8;
                longlong *plStack_2c0;
                longlong *plStack_2b8;
                undefined1 auStack_298 [168];
                longlong lStack_1f0;
                longlong *plStack_1e8;
                longlong lStack_1e0;
                undefined8 uStack_1d8;
                undefined2 uStack_1d0;
                undefined1 uStack_1ce;
                
/*   38-   38*/  sol_log_("Instruction: MigrateBondingCurveCreator",0x27);
/*   40-   40*/  uStack_3f1 = 0xff;
/*   48-   48*/  uStack_3f3 = 0xffff;
/*   a8-   a8*/  uStack_3f0 = param_3;
/*   a8-   a8*/  uStack_3e8 = param_4;
/*   a8-   a8*/  <pump_recovered::creator_migration::MigrateBondingCurveCreator_as_anchor_lang::Accounts<pump_recovered::creator_migration::MigrateBondingCurveCreatorBumps>>::try_accounts
/*   80-   a8*/            (&lStack_1f0,param_2,&uStack_3f0);
/*   a8-   a8*/  lVar2 = lStack_1e0;
/*   d8-   d8*/  if (lStack_1f0 != -0x8000000000000000) {
/*   e8-  108*/    memcpy(auStack_3c8,&uStack_1d8,0x1d8);
/*  110-  110*/    lStack_3d0 = lStack_1e0;
/*  118-  118*/    lStack_3d8 = (longlong)plStack_1e8;
/*  120-  120*/    lStack_3e0 = lStack_1f0;
/*  130-  130*/    uStack_1d0 = uStack_3f3;
/*  140-  140*/    uStack_1ce = uStack_3f1;
/*  150-  150*/    uStack_1d8 = uStack_3e8;
/*  160-  160*/    lStack_1e0 = uStack_3f0;
/*  170-  170*/    plStack_1e8 = &lStack_3e0;
/*  1a8-  1a8*/    lStack_1f0 = param_2;
/*  190-  1a8*/    pump_recovered::creator_migration::execute(&lStack_408,&lStack_1f0);
/*  1b8-  1b8*/    if (lStack_408 == 2) {
/*  200-  200*/      anchor_lang::accounts::account::Account<T>::exit_with_expected_owner
/*  1d0-  200*/                (&lStack_418,auStack_298,PUMP_PROGRAM_ID_1b79df,param_2);
/*  208-  218*/      lVar3 = 2;
/*  218-  218*/      if (lStack_418 != 2) {
/*  250-  250*/        anchor_lang::error::Error::with_account_name
/*  230-  250*/                  (&lStack_428,lStack_418,uStack_410,"bonding_curve",0xd);
/*  260-  260*/        lVar3 = lStack_428;
/*  260-  260*/        lVar2 = lStack_420;
                    }
/*  278-  278*/      lVar1 = *plStack_2f0;
/*  280-  288*/      *plStack_2f0 = lVar1 + -1;
/*  280-  290*/      if (lVar1 + -1 == 0) {
/*  298-  2a8*/        plStack_2f0[1] = plStack_2f0[1] + -1;
                    }
/*  2b0-  2b0*/      lVar1 = *plStack_2e8;
/*  2b8-  2c0*/      *plStack_2e8 = lVar1 + -1;
/*  2b8-  2c8*/      if (lVar1 + -1 == 0) {
/*  2d0-  2e0*/        plStack_2e8[1] = plStack_2e8[1] + -1;
                    }
/*  2f8-  2f8*/      lVar1 = *plStack_2c0;
/*  300-  308*/      *plStack_2c0 = lVar1 + -1;
/*  300-  310*/      if (lVar1 + -1 == 0) {
/*  318-  328*/        plStack_2c0[1] = plStack_2c0[1] + -1;
                    }
/*  330-  338*/      lVar1 = *plStack_2b8 + -1;
/*  340-  340*/      *plStack_2b8 = lVar1;
/*  348-  348*/      plStack_1e8 = (longlong *)lVar3;
/*  348-  348*/      lStack_1e0 = lVar2;
                  }
                  else {
/*  370-  370*/      lVar2 = *plStack_2f0;
/*  378-  380*/      *plStack_2f0 = lVar2 + -1;
/*  378-  388*/      if (lVar2 + -1 == 0) {
/*  390-  3a0*/        plStack_2f0[1] = plStack_2f0[1] + -1;
                    }
/*  3a8-  3a8*/      lVar2 = *plStack_2e8;
/*  3b0-  3b8*/      *plStack_2e8 = lVar2 + -1;
/*  3b0-  3c0*/      if (lVar2 + -1 == 0) {
/*  3c8-  3d8*/        plStack_2e8[1] = plStack_2e8[1] + -1;
                    }
/*  3f0-  3f0*/      lVar2 = *plStack_2c0;
/*  3f8-  400*/      *plStack_2c0 = lVar2 + -1;
/*  3f8-  408*/      if (lVar2 + -1 == 0) {
/*  410-  420*/        plStack_2c0[1] = plStack_2c0[1] + -1;
                    }
/*  428-  430*/      lVar1 = *plStack_2b8 + -1;
/*  438-  438*/      *plStack_2b8 = lVar1;
/*  440-  440*/      plStack_1e8 = (longlong *)lStack_408;
/*  440-  440*/      lStack_1e0 = lStack_400;
                  }
/*  348-  348*/    if (lVar1 == 0) {
/*  448-  458*/      plStack_2b8[1] = plStack_2b8[1] + -1;
                  }
                }
/*  468-  468*/  param_1[1] = lStack_1e0;
/*  470-  470*/  *param_1 = (longlong)plStack_1e8;
/*  478-  478*/  return;
              }
              
