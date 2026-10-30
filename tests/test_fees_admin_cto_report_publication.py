"""Real signed Fees CPI cases and actual report publication controls."""
import unittest
from publication_cli_support import PublicationCase

class FeesAdminCtoPublicationTests(PublicationCase,unittest.TestCase):
 NAMES=('fees_admin_cto_differential',)
 DATA=('evidence/upstream/pump_fees.json','evidence/upstream/pump.json','evidence/upstream/pump_amm.json',
       'research/imported-lab/analysis/pump_fun/config-snapshot.json',
       'evidence/original/pump/deployed.so','evidence/original/pump_amm/deployed.so','evidence/original/pump_fees/deployed.so',
       'evidence/dependencies/spl_token/deployed.so','evidence/dependencies/associated_token/deployed.so')
 HELPERS=('fees_donation_create_differential','fees_admin_differential','pump_validate_admin','pump_amm_admin_differential','pump_amm_reusable_harness')
 PROGRAM='evidence/original/pump_fees/deployed.so'
 EXPECTED={'fees_admin_cto_differential':63}
 LATE_INPUT='research/imported-lab/analysis/pump_fun/config-snapshot.json'

if __name__=='__main__':unittest.main()
