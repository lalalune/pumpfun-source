/*  bb8*/    pcStack_4a0 = *(char **)(pcVar46 + 0x19);
/*  bc8*/    ppppppplStack_4a8 = *(longlong ********)(pcVar46 + 0x11);
/*  bd8*/    pppppplStack_4b0 = *(longlong *******)(pcVar46 + 9);
/*  be8*/    uStack_4b8 = (char *)*plVar105;
/*  bf8*/    ppppppplStack_2b8 = (longlong *******)0x0;
/*  c00*/    ppppppplStack_2c0 = (longlong *******)0x0;
/*  c08*/    ppppppplStack_2c8 = (longlong *******)0x0;
/*  c10*/    ppppppplStack_2d0 = (longlong *******)0x0;
/*  c20*/    iVar39 = memcmp(&uStack_4b8,&ppppppplStack_2d0,0x20);
/*  c58*/    if (iVar39 == 0) {
/* 11d8*/      pump_recovered::PumpError::name(&uStack_488,&k_u32_30_1b5e04);
/* 11f8*/      ppppppplStack_460 = (longlong *******)0x0;
/* 1200*/      ppppppplStack_468 = (longlong *******)0x1;
/* 1208*/      ppppppplStack_470 = (longlong *******)0x0;
/* 1220*/      ppppppplStack_428 = (longlong *******)&obj_1bd838_1bd838;
/* 1230*/      ppppppplStack_430 = (longlong *******)&ppppppplStack_470;
/* 1240*/      ppppppplStack_418 = (longlong *******)CONCAT71(ppppppplStack_418._1_7_,3);
/* 1248*/      ppppppplStack_420 = (longlong *******)0x20;
/* 1250*/      ppppppplStack_440 = (longlong *******)0x0;
/* 1258*/      uStack_450 = (char *)0x0;
/* 1268*/      lVar47 = <pump_recovered::PumpError_as_core::fmt::Display>::fmt(&k_u32_30_1b5e04,&uStack_450);
/* 1288*/      if (lVar47 != 0) goto LAB_ram_00028118;
/*  c68*/    iVar39 = memcmp(&uStack_4b8,&ppppppplStack_518,0x20);
/*  ca0*/    if ((iVar39 == 0) || (iVar39 = memcmp(&uStack_4b8,&uStack_6a0,0x20), iVar39 == 0)) {
/*  cf8*/      pump_recovered::PumpError::name(&uStack_488,&k_u32_19_1b5e38);
/*  d18*/      ppppppplStack_460 = (longlong *******)0x0;
/*  d20*/      ppppppplStack_468 = (longlong *******)0x1;
/*  d28*/      ppppppplStack_470 = (longlong *******)0x0;
/*  d40*/      ppppppplStack_428 = (longlong *******)&obj_1bd838_1bd838;
/*  d50*/      ppppppplStack_430 = (longlong *******)&ppppppplStack_470;
/*  d60*/      ppppppplStack_418 = (longlong *******)CONCAT71(ppppppplStack_418._1_7_,3);
/*  d68*/      ppppppplStack_420 = (longlong *******)0x20;
/*  d70*/      ppppppplStack_440 = (longlong *******)0x0;
/*  d78*/      uStack_450 = (char *)0x0;
/*  d88*/      lVar47 = <pump_recovered::PumpError_as_core::fmt::Display>::fmt(&k_u32_19_1b5e38,&uStack_450);
/*  da8*/      if (lVar47 != 0) goto LAB_ram_00028118;
/* 10f8*/      ppppppplStack_288 = ppppppplStack_460;
/* 1108*/      uStack_290 = ppppppplStack_468;
/* 1118*/      ppppppplStack_298 = ppppppplStack_470;
/* 1128*/      ppppppplStack_2b0 = uStack_488;
/* 1138*/      ppppppplStack_2a8 = (longlong *******)uStack_480;
/* 1148*/      ppppppplStack_2a0 = (longlong *******)uStack_478;
/* 1160*/      ppppppplStack_2c8 = (longlong *******)0x1b68cc;
/* 1168*/      uStack_238 = CONCAT44(uStack_238._4_4_,0x1783);
/* 1170*/      plStack_280 = (longlong *)CONCAT71(plStack_280._1_7_,2);
/* 1178*/      ppppppplStack_2b8 = (longlong *******)CONCAT44(ppppppplStack_2b8._4_4_,0x138);
/* 1180*/      ppppppplStack_2c0 = (longlong *******)0x26;
/* 1188*/      ppppppplStack_2d0 = (longlong *******)0x0;
/* 11b0*/      <anchor_lang::error::Error_as_core::convert::From<anchor_lang::error::AnchorError>>::from
/* 1198*/                (&ppppppplStack_8a0,&ppppppplStack_2d0);
/* 11c8*/      ppppppplStack_6f0 = ppppppplStack_8a0;
/* 11c8*/      ppppppplStack_6e8 = ppppppplStack_898;
/* 1410*/    uStack_540._4_4_ = (undefined4)(CONCAT14(uStack_540._7_1_,*(undefined4 *)(pcVar46 + 4)) >> 8);
/* 1420*/    uStack_540 = (longlong *******)CONCAT44(uStack_540._4_4_,(int)*plVar105);
/* 1438*/    uVar59 = *(undefined8 *)(pcVar46 + 8);
/* 1440*/    uVar120 = *(undefined8 *)(pcVar46 + 0x10);
/* 1448*/    cStack_4e0 = pcVar46[0x20];
/* 1458*/    ppppppplStack_4e8 = *(longlong ********)(pcVar46 + 0x18);
/* 1480*/    if (param_4 != 0) {
/*  ad0*/      if (bVar97) goto LAB_ram_000234e0;
/*  ac0*/      if (bVar97) {
/*  ad0*/LAB_ram_000234e0:
/*  ad8*/        pump_recovered::PumpError::name(&ppppppplStack_2b0,&k_u32_91_1b5e08);
/*  af8*/        ppppppplStack_4a8 = (longlong *******)0x0;
/*  b00*/        pppppplStack_4b0 = (longlong ******)0x1;
/*  b08*/        uStack_4b8 = (char *)0x0;
/*  b20*/        ppppppplStack_428 = (longlong *******)&obj_1bd838_1bd838;
/*  b30*/        ppppppplStack_430 = (longlong *******)&uStack_4b8;
/*  b40*/        ppppppplStack_418 = (longlong *******)CONCAT71(ppppppplStack_418._1_7_,3);
/*  b48*/        ppppppplStack_420 = (longlong *******)0x20;
/*  b50*/        ppppppplStack_440 = (longlong *******)0x0;
/*  b58*/        uStack_450 = (char *)0x0;
/*  b80*/        lVar47 = <pump_recovered::PumpError_as_core::fmt::Display>::fmt
/*  b68*/                           (&k_u32_91_1b5e08,&uStack_450);
/*  b88*/        if (lVar47 != 0) goto LAB_ram_00028118;
