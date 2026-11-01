/*    0*//* WARNING: Type propagation algorithm not settling */
/*   28*/  puVar110 = *(undefined8 **)(param_2 + 8);
/*   30*/  puVar45 = *(undefined8 **)puVar110[2];
/*   40*/  pppppplStack_6a8 = (longlong ******)puVar45[3];
/*   50*/  uStack_6b0 = puVar45[2];
/*   60*/  uStack_6b8 = puVar45[1];
/*   70*/  pppppplStack_6c0 = (longlong ******)*puVar45;
/*   80*/  plVar105 = (longlong *)puVar110[0x12];
/*   88*/  puVar45 = (undefined8 *)*plVar105;
/*   90*/  ppppppplStack_2b8 = (longlong *******)puVar45[3];
/*   a0*/  ppppppplStack_2c0 = (longlong *******)puVar45[2];
/*   b0*/  ppppppplStack_2c8 = (longlong *******)puVar45[1];
/*   c0*/  ppppppplStack_2d0 = (longlong *******)*puVar45;
/*   d0*/  iVar39 = memcmp(puVar110[7] + 8,&ppppppplStack_2d0,0x20);
/*  100*/  uVar99 = 0;
/*  108*/  pcVar46 = *(char **)(param_5 + -0xff8);
/*  118*/  lVar47 = *(longlong *)(param_5 + -0x1000);
/*  138*/  if ((iVar39 == 0) && (iVar39 = memcmp(plVar105[3],PUMP_FEES_PROGRAM_ID_1b7a61,0x20), iVar39 == 0))
/*  338*/    iVar39 = memcmp(&uStack_450,NATIVE_MINT_1b5cc8,0x20);
/*  370*/    bVar97 = true;
/*  378*/    if (iVar39 != 0) {
/*  380*/      iVar39 = memcmp(puVar110[1] + 0x3a8,&uStack_450,0x20);
/*  3c0*/      bVar97 = true;
/*  3c8*/      if (iVar39 != 0) {
/*  3d0*/        bVar97 = false;
/*  3d8*/  uVar38 = uStack_10._4_4_;
/*  3e0*/  lVar48 = puVar110[1];
/*  3e8*/  cVar1 = *(char *)(lVar48 + 0x43e);
/*  3f0*/  uStack_20 = *(undefined8 *)(lVar106 + 0x20);
/*  400*/  pppppplStack_28 = *(longlong *******)(lVar106 + 0x18);
/*  410*/  ppppppplStack_30 = *(longlong ********)(lVar106 + 0x10);
/*  420*/  uStack_38 = *(char **)(lVar106 + 8);
/*  430*/  ppuVar100 = *(undefined8 ***)(lVar48 + 0x430);
/*  458*/  cVar2 = *(char *)(lVar106 + 0xa5);
/*  460*/  cVar3 = *(char *)(lVar106 + 0xa3);
/*  468*/  uStack_10._0_5_ = CONCAT41(uStack_10._4_4_,bVar97) << 0x18;
/*  438*/  uStack_10._0_5_ = CONCAT14(*(char *)(lVar48 + 0x43f),(undefined4)uStack_10);
/*  450*/  uStack_10 = CONCAT71(CONCAT61(CONCAT51(uStack_10._3_5_,cVar3),cVar2),*(char *)(lVar106 + 0xa2));
/*  450*/  if (*(char *)(lVar106 + 0xa2) != '\0') {
/*  438*/      if (*(char *)(lVar48 + 0x43f) == '\0') {
/*  480*/  *(bool *)(puVar110[7] + 0xa3) = (param_3 & 0xfd) == 0 && cVar3 != '\0';
