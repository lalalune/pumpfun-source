/*  c20*/    uStack_4b8._4_1_ = (undefined1)((uint)*(undefined4 *)(pbVar110 + 4) >> 8);
/*  c20*/    uStack_4b8._5_2_ = (undefined2)((uint)*(undefined4 *)(pbVar110 + 4) >> 0x10);
/*  c18*/    uStack_4b8._0_4_ = *(undefined4 *)(pbVar110 + 1);
/*  c10*/    uStack_4a1 = (undefined1)*(undefined8 *)(pbVar110 + 0x18);
/*  c10*/    uStack_4a0 = (undefined7)((ulonglong)*(undefined8 *)(pbVar110 + 0x18) >> 8);
/*  c50*/    bStack_499 = pbVar110[0x20];
/*  c68*/    uStack_4a9 = (undefined1)uVar121;
/*  c68*/    uStack_4a8 = (undefined7)((ulonglong)uVar121 >> 8);
/*  c78*/    uStack_4b8._7_1_ = (undefined1)uVar62;
/*  c78*/    uStack_4b0 = (undefined7)((ulonglong)uVar62 >> 8);
/*  c80*/    ppppppplStack_2b8 = (longlong *******)0x0;
/*  c88*/    ppppppplStack_2c0 = (longlong *******)0x0;
/*  c90*/    ppppppplStack_2c8 = (longlong *******)0x0;
/*  c98*/    ppppppplStack_2d0 = (longlong *******)0x0;
/*  ca8*/    iVar40 = memcmp(&uStack_4b8,&ppppppplStack_2d0,0x20);
/*  ce0*/    if (iVar40 == 0) {
/*  cf0*/    iVar40 = memcmp(&uStack_4b8,&ppppppplStack_518,0x20);
/*  d28*/    if ((iVar40 == 0) || (iVar40 = memcmp(&uStack_4b8,&ppppppplStack_470,0x20), iVar40 == 0)) {
/*  d88*/    bVar92 = cVar1 != '\0';
/*  dc0*/    if (uStack_920 != 0) {
/*  dd0*/      ppppppplStack_4e8 = ppppppplStack_30;
/*  dd8*/      ppppppplStack_530 = ppppppplStack_30;
/*  de8*/      ppppppplStack_4e0 = ppppppplStack_28;
/*  df0*/      ppppppplStack_528 = ppppppplStack_28;
/*  e00*/      ppppppplStack_4d8 = ppppppplStack_20;
/*  e08*/      ppppppplStack_520 = ppppppplStack_20;
/*  e18*/      ppppppplStack_918 = (longlong *******)uStack_38;
/*  e28*/      if (param_4 != 0) goto LAB_ram_00023f20;
/*  e40*/      uVar114 = 0;
/*  e48*/      bVar38 = false;
/*  b40*/      if (bVar101) goto LAB_ram_00023550;
/*  b00*/      uVar114 = 1;
/*  b08*/      bVar39 = 0;
/*  b20*/      bVar92 = false;
/*  b30*/      ppppppplStack_918 = ppppppplStack_6a0;
/*  b30*/      if (bVar101) {
/*  b40*/LAB_ram_00023550:
/*  b48*/        pump_recovered::PumpError::name(&ppppppplStack_2b0,&k_u32_91_1b5e08);
/*  b68*/        uStack_4a8 = 0;
/*  b68*/        uStack_4a1 = 0;
/*  b70*/        uStack_4b0 = 1;
/*  b70*/        uStack_4a9 = 0;
/*  b78*/        uStack_4b8._0_4_ = 0;
/*  b78*/        uStack_4b8._4_1_ = 0;
/*  b78*/        uStack_4b8._5_2_ = 0;
/*  b78*/        uStack_4b8._7_1_ = 0;
/*  b90*/        ppppppplStack_428 = (longlong *******)&obj_1bd838_1bd838;
/*  ba0*/        ppppppplStack_430 = (longlong *******)&uStack_4b8;
/*  bb0*/        ppppppplStack_418 = (longlong *******)CONCAT71(ppppppplStack_418._1_7_,3);
/*  bb8*/        ppppppplStack_420 = (longlong *******)0x20;
/*  bc0*/        ppppppplStack_440 = (longlong *******)0x0;
/*  bc8*/        uStack_450 = (char *)0x0;
/*  bf0*/        lVar50 = <pump_recovered::PumpError_as_core::fmt::Display>::fmt
/*  bd8*/                           (&k_u32_91_1b5e08,&uStack_450);
/*  bf8*/        if (lVar50 != 0) goto LAB_ram_00028150;
