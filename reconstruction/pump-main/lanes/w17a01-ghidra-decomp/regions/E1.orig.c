/*    0*//* WARNING: Type propagation algorithm not settling */
/*   28*/  plVar115 = *(longlong **)(param_2 + 8);
/*   30*/  puVar48 = *(undefined8 **)plVar115[2];
/*   40*/  pppppplStack_6a8 = (longlong ******)puVar48[3];
/*   50*/  uStack_6b0 = puVar48[2];
/*   60*/  uStack_6b8 = puVar48[1];
/*   70*/  pppppplStack_6c0 = (longlong ******)*puVar48;
/*   88*/  ppppppplStack_440 = &pppppplStack_6c0;
/*   a8*/  uStack_450 = "holder-rewards";
/*   b0*/  uStack_438 = 0x20;
/*   b8*/  ppppppplStack_448 = (longlong *******)0xe;
/*   f8*/  solana_pubkey::Pubkey::find_program_address
/*   c8*/            (&ppppppplStack_2d0,&uStack_450,2,PUMP_PROGRAM_ID_1b79df);
/*  108*/  ppppppplStack_688 = ppppppplStack_2b8;
/*  118*/  ppppppplStack_690 = ppppppplStack_2c0;
/*  128*/  ppppppplStack_698 = ppppppplStack_2c8;
/*  138*/  ppppppplStack_6a0 = ppppppplStack_2d0;
/*  140*/  lVar120 = plVar115[7];
/*  148*/  plVar49 = (longlong *)plVar115[0x12];
/*  158*/  puVar48 = (undefined8 *)*plVar49;
/*  160*/  ppppppplStack_2b8 = (longlong *******)puVar48[3];
/*  170*/  ppppppplStack_2c0 = (longlong *******)puVar48[2];
/*  180*/  ppppppplStack_2c8 = (longlong *******)puVar48[1];
/*  190*/  ppppppplStack_2d0 = (longlong *******)*puVar48;
/*  1a8*/  iVar40 = memcmp(lVar120 + 8,&ppppppplStack_2d0,0x20);
/*  1d8*/  uStack_920 = 0;
/*  1e0*/  pbVar110 = *(byte **)(param_5 + -0xff8);
/*  1e8*/  lVar50 = *(longlong *)(param_5 + -0x1000);
/*  208*/  if ((iVar40 == 0) && (iVar40 = memcmp(plVar49[3],PUMP_FEES_PROGRAM_ID_1b7a61,0x20), iVar40 == 0))
/*  260*/    uStack_920 = solana_account_info::AccountInfo::data_is_empty(plVar49);
/*  268*/    lVar120 = plVar115[7];
/*  270*/    uStack_920 = uStack_920 ^ 1;
