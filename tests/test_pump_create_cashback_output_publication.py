"""Real create/cashback programs preserve every consumed file during publication."""
import unittest
from publication_cli_support import PublicationCase

class CreateCashbackPublicationTests(PublicationCase,unittest.TestCase):
 NAMES=('pump_create_differential','pump_cashback_differential')
 PROGRAM='evidence/original/pump/deployed.so'
 COMMON=('evidence/upstream/pump.json',PROGRAM)
 CREATE=(*COMMON,'research/imported-lab/analysis/pump_fun/config-snapshot.json',
         'evidence/original/mayhem/deployed.so',*(f'evidence/dependencies/{n}/deployed.so' for n in ('spl_token','spl_token_2022','associated_token','token_metadata')))
 CASHBACK=(*COMMON,'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json',
           *(f'evidence/{group}/{name}/{file}' for group,names in [('original',('pump','pump_fees')),('dependencies',('spl_token','spl_token_2022','associated_token'))] for name in names for file in ('capture.json','deployed.so')))
 DATA=tuple(dict.fromkeys((*CREATE,*CASHBACK)))
 INPUTS={'pump_create_differential':CREATE,'pump_cashback_differential':CASHBACK}
 HELPERS={'pump_create_differential':('pump_amm_reusable_harness',), 'pump_cashback_differential':('pump_amm_reusable_harness','pump_trade_fixture')}
 EXPECTED={'pump_create_differential':87,'pump_cashback_differential':283}
 LATE_INPUT={'pump_create_differential':'evidence/dependencies/token_metadata/deployed.so','pump_cashback_differential':'evidence/dependencies/spl_token/capture.json'}

if __name__=='__main__':unittest.main()
