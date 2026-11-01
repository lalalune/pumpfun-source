/* 5b48*/        plVar81 = plVar115 + 0x15;
/* 5b58*/        puVar48 = (undefined8 *)**(undefined8 **)(plVar115[3] + 0x58);
/* 5b70*/        ppppppplStack_2b8 = (longlong *******)puVar48[3];
/* 5b80*/        ppppppplStack_2c0 = (longlong *******)puVar48[2];
/* 5b90*/        ppppppplStack_2c8 = (longlong *******)puVar48[1];
/* 5ba0*/        ppppppplStack_2d0 = (longlong *******)*puVar48;
/* 5bb8*/        iVar40 = memcmp(&ppppppplStack_2d0,NATIVE_MINT_1b5cc8,0x20);
/* 5be8*/        lVar120 = solana_account_info::AccountInfo::data_is_empty(plVar115[0x11]);
/* 5c10*/        if (iVar40 == 0) {
/* 5a20*/          ppppppplVar122 = (longlong *******)0x0;
/* 5a38*/          ppppppplStack_6e0 = (longlong *******)0x2;
/* 5a48*/          if (ppppppplVar46 < ppppppplVar97) {
/* 5a80*/            pump_recovered::legacy_native_payments::ensure_rent_exempt
/* 5a60*/                      (&ppppppplStack_840,plVar49,plVar115,plVar81);
/* 5a90*/            ppppppplStack_6e0 = ppppppplStack_840;
/* 5a90*/            ppppppplStack_7d8 = ppppppplStack_838;
/* 5a90*/            if (ppppppplStack_840 == (longlong *******)0x2) {
/* 5af0*/              pump_recovered::payments::collect_transfer_native
/* 5a38*/              ppppppplStack_6e0 = (longlong *******)0x2;
/* 5b10*/              ppppppplStack_7d8 = ppppppplVar122;
/* 5b10*/              if (ppppppplStack_850 != (longlong *******)0x2) {
/* 5b28*/                ppppppplStack_6e0 = ppppppplStack_850;
/* 5b28*/                ppppppplStack_7d8 = ppppppplStack_848;
