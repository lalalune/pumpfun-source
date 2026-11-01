/* 5b30*/        puVar45 = puVar110 + 0x15;
/* 5b40*/        puVar91 = (undefined8 *)**(undefined8 **)(puVar110[3] + 0x58);
/* 5b58*/        ppppppplStack_2b8 = (longlong *******)puVar91[3];
/* 5b68*/        ppppppplStack_2c0 = (longlong *******)puVar91[2];
/* 5b78*/        ppppppplStack_2c8 = (longlong *******)puVar91[1];
/* 5b88*/        ppppppplStack_2d0 = (longlong *******)*puVar91;
/* 5ba0*/        iVar39 = memcmp(&ppppppplStack_2d0,NATIVE_MINT_1b5cc8,0x20);
/* 5bd0*/        uVar99 = solana_account_info::AccountInfo::data_is_empty(puVar110[0x11]);
/* 5bf8*/        if (iVar39 == 0) {
/* 59e8*/            ppppppplVar83 = (longlong *******)0x0;
/* 59f8*/              ppppppplVar83 =
/* 5a10*/            ppppppplVar69 = ppppppplVar83;
/* 5a00*/            ppppppplStack_6f0 = (longlong *******)0x2;
/* 5a10*/            if (((ppppppplVar102 < ppppppplVar109) &&
/* 5a50*/                (pump_recovered::legacy_native_payments::ensure_rent_exempt
/* 5a30*/                           (&ppppppplStack_840,plVar105,puVar110,puVar45),
/* 5a60*/                ppppppplVar69 = ppppppplStack_838, ppppppplStack_6f0 = ppppppplStack_840,
/* 5a60*/                ppppppplStack_840 == (longlong *******)0x2)) &&
/* 5ac0*/               (pump_recovered::payments::collect_transfer_native
/* 5a00*/               ppppppplVar69 = ppppppplVar83, ppppppplStack_6f0 = (longlong *******)0x2,
/* 5ae0*/               ppppppplStack_850 != (longlong *******)0x2)) {
/* 5af0*/              ppppppplVar69 = ppppppplStack_848;
/* 5af0*/              ppppppplStack_6f0 = ppppppplStack_850;
/* 5af8*/                    if (ppppppplStack_820 == (longlong *******)0x2) goto joined_r0x00028508;
/* 5af8*/joined_r0x00028508:
/* 5af8*/    ppppppplStack_6e8 = ppppppplVar69;
