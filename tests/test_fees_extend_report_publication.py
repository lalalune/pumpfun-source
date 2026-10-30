"""Real Fees extension cases and input-preserving publication controls."""
import unittest
from publication_cli_support import PublicationCase

class FeesExtendPublicationTests(PublicationCase,unittest.TestCase):
 NAMES=('fees_extend_differential',)
 DATA=('evidence/upstream/pump_fees.json','evidence/original/pump_fees/deployed.so')
 HELPERS=('fees_admin_differential','fees_config_differential','fee_recovery_fixture')
 PROGRAM='evidence/original/pump_fees/deployed.so'
 EXPECTED={'fees_extend_differential':297}

if __name__=='__main__':unittest.main()
