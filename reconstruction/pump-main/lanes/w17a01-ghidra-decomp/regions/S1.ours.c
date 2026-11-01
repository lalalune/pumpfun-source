/* 1580*/      goto LAB_ram_00023f90;
/* 1580*/LAB_ram_00023f90:
/* 1590*/      if (cVar1 == '\0') {
/* 25e8*/        if (*(char *)((longlong)puVar110 + 0xd1) == '\0') {
/* 25f8*/        pump_recovered::admin_cto::token_frozen(&ppppppplStack_2d0,puVar110[8]);
/* 2620*/        ppppppplStack_6f0 = ppppppplStack_2d0;
/* 2620*/        ppppppplStack_6e8 = ppppppplStack_2c8;
/* 2620*/        if (ppppppplStack_2d0 != (longlong *******)0x2) goto LAB_ram_00028248;
/* 2630*/        if ((char)ppppppplStack_2c8 != '\0') {
/* 2638*/          pcVar46 = "Creator quote token account is frozen; fees left in the vaults";
/* 2648*/          uVar99 = 0x3e;
/* 1f50*/      lVar106 = solana_account_info::AccountInfo::data_is_empty(puVar110[0x11]);
/* 1f60*/      if (lVar106 == 0) {
/* 2480*/        pump_recovered::admin_cto::token_frozen(&ppppppplStack_2d0,puVar110[0x11]);
/* 24a8*/        ppppppplVar69 = ppppppplStack_2c8;
/* 24a8*/        ppppppplStack_6f0 = ppppppplStack_2d0;
/* 24a8*/        if (ppppppplStack_2d0 == (longlong *******)0x2) {
/* 1f70*/          if ((char)ppppppplStack_2c8 == '\0') goto LAB_ram_00024980;
/* 24c8*/          pump_recovered::admin_cto::token_raw_amount(&ppppppplStack_2d0,puVar110[0x11]);
/* 24f0*/          ppppppplVar69 = ppppppplStack_2c8;
/* 24f0*/          ppppppplStack_6f0 = ppppppplStack_2d0;
/* 24f0*/          if (ppppppplStack_2d0 == (longlong *******)0x2) {
/* 1f90*/            if (ppppppplStack_2c8 == (longlong *******)0x0) goto LAB_ram_000249a0;
/* 2510*/            pump_recovered::PumpError::name(&ppppppplStack_2b0,&k_u32_93_1b5e50);
/* 2538*/            <T_as_alloc::string::ToString>::to_string(&ppppppplStack_298,&k_u32_93_1b5e50);
/* 2568*/            ppppppplStack_2c8 = (longlong *******)0x1b68cc;
/* 2570*/            plStack_280 = (longlong *)CONCAT71(plStack_280._1_7_,2);
/* 2578*/            ppppppplStack_2b8 = (longlong *******)CONCAT44(ppppppplStack_2b8._4_4_,0x294);
/* 2580*/            ppppppplStack_2c0 = (longlong *******)0x26;
/* 2588*/            ppppppplStack_2d0 = (longlong *******)0x0;
/* 2590*/            uStack_238 = CONCAT44(uStack_238._4_4_,0x17cd);
/* 25b8*/            <anchor_lang::error::Error_as_core::convert::From<anchor_lang::error::AnchorError>>::from
/* 25a0*/                      (&ppppppplStack_7e0,&ppppppplStack_2d0);
/* 25d0*/            ppppppplVar69 = ppppppplStack_7d8;
/* 25d0*/            ppppppplStack_6f0 = ppppppplStack_7e0;
/* 1f70*/LAB_ram_00024980:
/* 1f70*/        lVar106 = solana_account_info::AccountInfo::data_is_empty(puVar110[0x11]);
/* 1f80*/        if (lVar106 == 0) {
/* 2658*/          puVar91 = (undefined8 *)puVar110[0xb];
/* 2660*/          ppppppplVar102 = (longlong *******)puVar91[1];
/* 2668*/          pppppplVar62 = *ppppppplVar102;
/* 2690*/          ppppppplVar69 = (longlong *******)*puVar91;
/* 2698*/          ppppppplVar83 = (longlong *******)puVar91[3];
/* 2670*/          *ppppppplVar102 = (longlong ******)((longlong)pppppplVar62 + 1);
/* 2670*/          if ((longlong ******)((longlong)pppppplVar62 + 1) == (longlong ******)0x0)
/* 26b0*/          goto LAB_ram_000250c0;
/* 26b8*/          ppppppplVar109 = (longlong *******)puVar91[2];
/* 26c0*/          pppppplVar62 = *ppppppplVar109;
/* 26c8*/          *ppppppplVar109 = (longlong ******)((longlong)pppppplVar62 + 1);
/* 26c8*/          if ((longlong ******)((longlong)pppppplVar62 + 1) == (longlong ******)0x0)
/* 26b0*/          goto LAB_ram_000250c0;
/* 26b0*/          if (lVar106 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar106 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar41 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar52 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar52 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar52 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar52 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar52 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar52 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar52 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/          if (lVar52 + 1 == 0) goto LAB_ram_000250c0;
/* 1f90*/LAB_ram_000249a0:
/* 1f90*/        puVar91 = (undefined8 *)puVar110[0x15];
/* 1f98*/        pcStack_4a0 = (char *)puVar91[3];
/* 1fa8*/        ppppppplStack_4a8 = (longlong *******)puVar91[2];
/* 1fb8*/        pppppplStack_4b0 = (longlong ******)puVar91[1];
/* 1fc8*/        uStack_4b8 = (char *)*puVar91;
/* 1fe0*/        uStack_488 = (longlong *******)&uStack_38;
/* 1ff8*/        ppuStack_18 = &puStack_4d0;
/* 2010*/        pppppplStack_28 = (longlong ******)&uStack_4b8;
/* 2030*/        uStack_38 = "creator-vault";
/* 2038*/        puStack_4d0 = (undefined8 *)CONCAT71(puStack_4d0._1_7_,uVar98);
/* 2040*/        uStack_480 = 3;
/* 2048*/        uStack_10 = 1;
/* 2050*/        uStack_20 = 0x20;
/* 2058*/        ppppppplStack_30 = (longlong *******)0xd;
/* 2078*/        if (iVar39 == 0) {
/* 2080*/          pump_recovered::admin_cto::token_frozen(&ppppppplStack_2d0,puVar110[9]);
/* 20a8*/          ppppppplVar69 = ppppppplStack_2c8;
/* 20a8*/          ppppppplStack_6f0 = ppppppplStack_2d0;
/* 20a8*/          if (ppppppplStack_2d0 == (longlong *******)0x2) {
/* 20d0*/            cVar2 = (char)ppppppplStack_2c8;
/* 20c8*/            pump_recovered::admin_cto::token_raw_amount(&ppppppplStack_2d0,puVar110[9]);
/* 20f0*/            ppppppplVar83 = ppppppplStack_2c8;
/* 2108*/            ppppppplVar69 = ppppppplVar83;
/* 2108*/            ppppppplStack_6f0 = ppppppplStack_2d0;
/* 2108*/            if (ppppppplStack_2d0 == (longlong *******)0x2) {
/* 2128*/              if (cVar2 == '\0') {
/* 20c8*/                              (&ppppppplStack_820,puVar110 + 4,puVar110 + 9,puVar110 + 10);
/* 2130*/                ppppppplVar69 = (longlong *******)0x0;
/* 2138*/                ppppppplStack_6f0 = (longlong *******)0x2;
/* 2140*/                if (ppppppplStack_2c8 != (longlong *******)0x0) {
/* 2150*/                  pump_recovered::PumpError::name(&ppppppplStack_2b0,&k_u32_93_1b5e50);
/* 2178*/                  <T_as_alloc::string::ToString>::to_string(&ppppppplStack_298,&k_u32_93_1b5e50);
/* 21a8*/                  ppppppplStack_2c8 = (longlong *******)0x1b68cc;
/* 21b0*/                  plStack_280 = (longlong *)CONCAT71(plStack_280._1_7_,2);
/* 21b8*/                  ppppppplStack_2b8 = (longlong *******)CONCAT44(ppppppplStack_2b8._4_4_,0x2cf);
/* 21c0*/                  ppppppplStack_2c0 = (longlong *******)0x26;
/* 21c8*/                  ppppppplStack_2d0 = (longlong *******)0x0;
/* 21d0*/                  uStack_238 = CONCAT44(uStack_238._4_4_,0x17cd);
/* 21f8*/                  <anchor_lang::error::Error_as_core::convert::From<anchor_lang::error::AnchorError>>::from
/* 21e0*/                            (&ppppppplStack_800,&ppppppplStack_2d0);
/* 2210*/                  ppppppplVar69 = ppppppplStack_7f8;
/* 2210*/                  ppppppplStack_6f0 = ppppppplStack_800;
/* 2220*/      anchor_lang::error::ErrorCode::name(&uStack_4b8,&k_u32_2006_1b5e9c);
/* 2240*/      pppppplStack_28 = (longlong ******)0x0;
/* 2248*/      ppppppplStack_30 = (longlong *******)0x1;
/* 2250*/      uStack_38 = (char *)0x0;
/* 2268*/      ppppppplStack_428 = (longlong *******)&obj_1bd838_1bd838;
/* 2278*/      ppppppplStack_430 = (longlong *******)&uStack_38;
/* 2288*/      ppppppplStack_418 = (longlong *******)CONCAT71(ppppppplStack_418._1_7_,3);
/* 2290*/      ppppppplStack_420 = (longlong *******)0x20;
/* 2298*/      ppppppplStack_440 = (longlong *******)0x0;
/* 22a0*/      uStack_450 = (char *)0x0;
/* 22c8*/      lVar106 = <anchor_lang::error::ErrorCode_as_core::fmt::Display>::fmt
/* 22b0*/                          (&k_u32_2006_1b5e9c,&uStack_450);
/* 22d0*/      if (lVar106 != 0) {
/* 22e8*/      ppppppplStack_288 = (longlong *******)pppppplStack_28;
/* 22f8*/      uStack_290 = ppppppplStack_30;
/* 2308*/      ppppppplStack_298 = (longlong *******)uStack_38;
/* 2318*/      ppppppplStack_2b0 = (longlong *******)uStack_4b8;
/* 2328*/      ppppppplStack_2a8 = (longlong *******)pppppplStack_4b0;
/* 2338*/      ppppppplStack_2a0 = ppppppplStack_4a8;
/* 2350*/      ppppppplStack_2c8 = (longlong *******)0x1b68cc;
/* 2358*/      uStack_238 = CONCAT44(uStack_238._4_4_,0x7d6);
/* 2360*/      plStack_280 = (longlong *)CONCAT71(plStack_280._1_7_,2);
/* 2368*/      ppppppplStack_2b8 = (longlong *******)CONCAT44(ppppppplStack_2b8._4_4_,0x288);
/* 2370*/      ppppppplStack_2c0 = (longlong *******)0x26;
/* 2378*/      ppppppplStack_2d0 = (longlong *******)0x0;
/* 23a0*/      <anchor_lang::error::Error_as_core::convert::From<anchor_lang::error::AnchorError>>::from
/* 2388*/                (&uStack_7c0,&ppppppplStack_2d0);
/* 23b8*/      puVar45 = (undefined8 *)*puVar45;
/* 23c0*/      ppppppplStack_2b8 = (longlong *******)puVar45[3];
/* 23d0*/      ppppppplStack_2c0 = (longlong *******)puVar45[2];
/* 23e0*/      ppppppplStack_2c8 = (longlong *******)puVar45[1];
/* 23f0*/      ppppppplStack_2d0 = (longlong *******)*puVar45;
/* 2408*/      ppppppplStack_2b0 = ppppppplStack_518;
/* 2418*/      ppppppplStack_2a8 = ppppppplStack_510;
/* 2428*/      ppppppplStack_2a0 = ppppppplStack_508;
/* 2438*/      ppppppplStack_298 = (longlong *******)pppppplStack_500;
/* 2460*/      anchor_lang::error::Error::with_pubkeys
/* 2448*/                (&ppppppplStack_7d0,uStack_7c0,uStack_7b8,&ppppppplStack_2d0);
/* 2478*/      ppppppplVar69 = ppppppplStack_7c8;
/* 2478*/      ppppppplStack_6f0 = ppppppplStack_7d0;
/* 26b0*/LAB_ram_000250c0:
/* 26b0*/                    /* WARNING: Subroutine does not return */
/* 26b0*/      abort();
/* 26b0*/    goto LAB_ram_000250c0;
/* 26b0*/    if (lVar106 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/    if (lVar106 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/    if (lVar73 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/    if (lVar73 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/    if (lVar73 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/    if (lVar73 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/    if (lVar73 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/    if (lVar73 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/    if (lVar73 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/    if (lVar73 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/    if (lVar73 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/    if (lVar73 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/    if (lVar73 + 1 == 0) goto LAB_ram_000250c0;
/* 26b0*/    if (lVar73 + 1 == 0) goto LAB_ram_000250c0;
