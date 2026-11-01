/* 2620*/        if (*(char *)((longlong)plVar115 + 0xd1) == '\0') {
/* 2630*/        pump_recovered::admin_cto::token_frozen(&ppppppplStack_2d0,plVar115[8]);
/* 2658*/        ppppppplStack_6e0 = ppppppplStack_2d0;
/* 2658*/        ppppppplStack_6c8 = ppppppplStack_2c8;
/* 2658*/        if (ppppppplStack_2d0 != (longlong *******)0x2) goto LAB_ram_00028280;
/* 2668*/        if ((byte)ppppppplStack_2c8 != '\0') {
/* 2670*/          msg = "Creator quote token account is frozen; fees left in the vaults";
/* 2680*/          len = 0x3e;
/* 1f78*/      lVar120 = solana_account_info::AccountInfo::data_is_empty(plVar115[0x11]);
/* 1f88*/      if (lVar120 == 0) {
/* 24b8*/        pump_recovered::admin_cto::token_frozen(&ppppppplStack_2d0,plVar115[0x11]);
/* 24e0*/        ppppppplStack_6e0 = ppppppplStack_2d0;
/* 24e0*/        ppppppplStack_6c8 = ppppppplStack_2c8;
/* 24e0*/        if (ppppppplStack_2d0 != (longlong *******)0x2) goto LAB_ram_00028280;
/* 1f98*/        if ((byte)ppppppplStack_2c8 == '\0') goto LAB_ram_000249a8;
/* 2500*/        pump_recovered::admin_cto::token_raw_amount(&ppppppplStack_2d0,plVar115[0x11]);
/* 2528*/        ppppppplStack_6e0 = ppppppplStack_2d0;
/* 2528*/        ppppppplStack_6c8 = ppppppplStack_2c8;
/* 2528*/        if (ppppppplStack_2d0 != (longlong *******)0x2) goto LAB_ram_00028280;
/* 2538*/        if (ppppppplStack_2c8 != (longlong *******)0x0) {
/* 2548*/          pump_recovered::PumpError::name(&ppppppplStack_2b0,&k_u32_93_1b5e50);
/* 2570*/          <T_as_alloc::string::ToString>::to_string(&ppppppplStack_298,&k_u32_93_1b5e50);
/* 25a0*/          ppppppplStack_2c8 = (longlong *******)0x1b68cc;
/* 25a8*/          plStack_280 = (longlong *)CONCAT71(plStack_280._1_7_,2);
/* 25b0*/          ppppppplStack_2b8 = (longlong *******)CONCAT44(ppppppplStack_2b8._4_4_,0x294);
/* 25b8*/          ppppppplStack_2c0 = (longlong *******)0x26;
/* 25c0*/          ppppppplStack_2d0 = (longlong *******)0x0;
/* 25c8*/          uStack_238 = CONCAT44(uStack_238._4_4_,0x17cd);
/* 25f0*/          <anchor_lang::error::Error_as_core::convert::From<anchor_lang::error::AnchorError>>::from
/* 25d8*/                    (&ppppppplStack_7e0,&ppppppplStack_2d0);
/* 2610*/          ppppppplStack_6e0 = ppppppplStack_7e0;
/* 2610*/          goto joined_r0x00025020;
/* 1f98*/LAB_ram_000249a8:
/* 1f98*/        lVar120 = solana_account_info::AccountInfo::data_is_empty(plVar115[0x11]);
/* 1fa8*/        if (lVar120 == 0) {
/* 2690*/          puVar48 = (undefined8 *)plVar115[0xb];
/* 2698*/          ppppppplVar122 = (longlong *******)puVar48[1];
/* 26a0*/          pppppplVar74 = *ppppppplVar122;
/* 26c8*/          ppppppplVar46 = (longlong *******)*puVar48;
/* 26a8*/          *ppppppplVar122 = (longlong ******)((longlong)pppppplVar74 + 1);
/* 26a8*/          if ((longlong ******)((longlong)pppppplVar74 + 1) == (longlong ******)0x0)
/* 26e0*/          goto LAB_ram_000250f0;
/* 26e0*/          goto LAB_ram_000250f0;
/* 26e0*/          if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar60 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar60 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar60 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar60 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar53 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar53 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar65 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar65 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar65 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar65 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar65 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/          if (lVar65 + 1 == 0) goto LAB_ram_000250f0;
/* 1fb8*/      puVar48 = (undefined8 *)plVar115[0x15];
/* 1fc0*/      uStack_4a0 = (undefined7)puVar48[3];
/* 1fc0*/      bStack_499 = (byte)((ulonglong)puVar48[3] >> 0x38);
/* 1fd0*/      uStack_4a8 = (undefined7)puVar48[2];
/* 1fd0*/      uStack_4a1 = (undefined1)((ulonglong)puVar48[2] >> 0x38);
/* 1fe0*/      uStack_4b0 = (undefined7)puVar48[1];
/* 1fe0*/      uStack_4a9 = (undefined1)((ulonglong)puVar48[1] >> 0x38);
/* 1ff0*/      uVar98 = *puVar48;
/* 1ff8*/      uStack_4b8._0_4_ = (undefined4)uVar98;
/* 1ff8*/      uStack_4b8._4_1_ = (undefined1)((ulonglong)uVar98 >> 0x20);
/* 1ff8*/      uStack_4b8._5_2_ = (undefined2)((ulonglong)uVar98 >> 0x28);
/* 1ff8*/      uStack_4b8._7_1_ = (undefined1)((ulonglong)uVar98 >> 0x38);
/* 2008*/      uStack_488 = (longlong *******)&uStack_38;
/* 2020*/      pppppplStack_18 = (longlong ******)&pppppplStack_4d0;
/* 2038*/      ppppppplStack_28 = (longlong *******)&uStack_4b8;
/* 2058*/      uStack_38 = "creator-vault";
/* 2068*/      pppppplStack_4d0 = (longlong ******)CONCAT71(pppppplStack_4d0._1_7_,uVar5);
/* 2070*/      uStack_480 = 3;
/* 2078*/      uStack_10 = 1;
/* 2080*/      ppppppplStack_20 = (longlong *******)0x20;
/* 2088*/      ppppppplStack_30 = (longlong *******)0xd;
/* 20a8*/      if (iVar40 == 0) {
/* 20b0*/        pump_recovered::admin_cto::token_raw_amount(&ppppppplStack_2d0,plVar115[9]);
/* 20c8*/        ppppppplVar122 = ppppppplStack_2c8;
/* 20d8*/        ppppppplStack_6e0 = ppppppplStack_2d0;
/* 20d8*/        ppppppplStack_7d8 = ppppppplStack_2c8;
/* 20d8*/        if (ppppppplStack_2d0 == (longlong *******)0x2) {
/* 20e8*/          pump_recovered::admin_cto::token_frozen(&ppppppplStack_2d0,plVar115[9]);
/* 2120*/          ppppppplStack_6e0 = ppppppplStack_2d0;
/* 2120*/          ppppppplStack_7d8 = ppppppplStack_2c8;
/* 2120*/          if (ppppppplStack_2d0 == (longlong *******)0x2) {
/* 2140*/            if ((byte)ppppppplStack_2c8 == '\0') {
/* 20e8*/                            (&ppppppplStack_820,plVar115 + 4,plVar115 + 9,plVar115 + 10);
/* 2150*/              ppppppplStack_6e0 = (longlong *******)0x2;
/* 2148*/              ppppppplStack_7d8 = (longlong *******)0x0;
/* 2160*/              if (ppppppplVar122 != (longlong *******)0x0) {
/* 2170*/                pump_recovered::PumpError::name(&ppppppplStack_2b0,&k_u32_93_1b5e50);
/* 2198*/                <T_as_alloc::string::ToString>::to_string(&ppppppplStack_298,&k_u32_93_1b5e50);
/* 21c8*/                ppppppplStack_2c8 = (longlong *******)0x1b68cc;
/* 21d0*/                plStack_280 = (longlong *)CONCAT71(plStack_280._1_7_,2);
/* 21d8*/                ppppppplStack_2b8 = (longlong *******)CONCAT44(ppppppplStack_2b8._4_4_,0x2cf);
/* 21e0*/                ppppppplStack_2c0 = (longlong *******)0x26;
/* 21e8*/                ppppppplStack_2d0 = (longlong *******)0x0;
/* 21f0*/                uStack_238 = CONCAT44(uStack_238._4_4_,0x17cd);
/* 2218*/                <anchor_lang::error::Error_as_core::convert::From<anchor_lang::error::AnchorError>>::from
/* 2200*/                          (&ppppppplStack_800,&ppppppplStack_2d0);
/* 2230*/                ppppppplStack_6e0 = ppppppplStack_800;
/* 2230*/                ppppppplStack_7d8 = ppppppplStack_7f8;
/* 2240*/      anchor_lang::error::ErrorCode::name(&uStack_4b8,&k_u32_2006_1b5e9c);
/* 2260*/      ppppppplStack_28 = (longlong *******)0x0;
/* 2268*/      ppppppplStack_30 = (longlong *******)0x1;
/* 2270*/      uStack_38 = (char *)0x0;
/* 2288*/      ppppppplStack_428 = (longlong *******)&obj_1bd838_1bd838;
/* 2298*/      ppppppplStack_430 = (longlong *******)&uStack_38;
/* 22a8*/      ppppppplStack_418 = (longlong *******)CONCAT71(ppppppplStack_418._1_7_,3);
/* 22b0*/      ppppppplStack_420 = (longlong *******)0x20;
/* 22b8*/      ppppppplStack_440 = (longlong *******)0x0;
/* 22c0*/      uStack_450 = (char *)0x0;
/* 22e8*/      lVar120 = <anchor_lang::error::ErrorCode_as_core::fmt::Display>::fmt
/* 22d0*/                          (&k_u32_2006_1b5e9c,&uStack_450);
/* 22f0*/      if (lVar120 != 0) {
/* 2308*/      ppppppplStack_288 = ppppppplStack_28;
/* 2318*/      uStack_290 = ppppppplStack_30;
/* 2328*/      ppppppplStack_298 = (longlong *******)uStack_38;
/* 2330*/      ppppppplStack_2b0 =
/* 2330*/           CONCAT17(uStack_4b8._7_1_,
/* 2330*/                    CONCAT25(uStack_4b8._5_2_,CONCAT14(uStack_4b8._4_1_,(undefined4)uStack_4b8)));
/* 2340*/      ppppppplStack_2a8 = (longlong *******)CONCAT17(uStack_4a9,uStack_4b0);
/* 2350*/      ppppppplStack_2a0 = (longlong *******)CONCAT17(uStack_4a1,uStack_4a8);
/* 2370*/      ppppppplStack_2c8 = (longlong *******)0x1b68cc;
/* 2378*/      uStack_238 = CONCAT44(uStack_238._4_4_,0x7d6);
/* 2380*/      plStack_280 = (longlong *)CONCAT71(plStack_280._1_7_,2);
/* 2388*/      ppppppplStack_2b8 = (longlong *******)CONCAT44(ppppppplStack_2b8._4_4_,0x288);
/* 2390*/      ppppppplStack_2c0 = (longlong *******)0x26;
/* 2398*/      ppppppplStack_2d0 = (longlong *******)0x0;
/* 23c0*/      <anchor_lang::error::Error_as_core::convert::From<anchor_lang::error::AnchorError>>::from
/* 23a8*/                (&uStack_7c0,&ppppppplStack_2d0);
/* 23e0*/      puVar48 = (undefined8 *)*plVar81;
/* 23e8*/      ppppppplStack_2b8 = (longlong *******)puVar48[3];
/* 23f8*/      ppppppplStack_2c0 = (longlong *******)puVar48[2];
/* 2408*/      ppppppplStack_2c8 = (longlong *******)puVar48[1];
/* 2418*/      ppppppplStack_2d0 = (longlong *******)*puVar48;
/* 2430*/      ppppppplStack_2b0 = ppppppplStack_518;
/* 2440*/      ppppppplStack_2a8 = ppppppplStack_510;
/* 2450*/      ppppppplStack_2a0 = ppppppplStack_508;
/* 2460*/      ppppppplStack_298 = ppppppplStack_500;
/* 2488*/      anchor_lang::error::Error::with_pubkeys
/* 2470*/                (&ppppppplStack_7d0,uStack_7c0,uStack_7b8,&ppppppplStack_2d0);
/* 24a8*/      ppppppplStack_6e0 = ppppppplStack_7d0;
/* 24a8*/      ppppppplStack_7d8 = ppppppplStack_7c8;
/* 2610*/joined_r0x00025020:
/* 2610*/    ppppppplVar122 = ppppppplStack_7d8;
/* 2610*/    ppppppplStack_6c8 = ppppppplVar122;
/* 2610*/    if (ppppppplStack_6e0 != (longlong *******)0x2) goto LAB_ram_00028280;
/* 26e0*/LAB_ram_000250f0:
/* 26e0*/                    /* WARNING: Subroutine does not return */
/* 26e0*/      abort();
/* 26e0*/    goto LAB_ram_000250f0;
/* 26e0*/    if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/    if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/    if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/    if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/    if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/    if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/    if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/    if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/    if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/    if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/    if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/    if (lVar120 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/    if (lVar68 + 1 == 0) goto LAB_ram_000250f0;
/* 26e0*/    if (lVar68 + 1 == 0) goto LAB_ram_000250f0;
