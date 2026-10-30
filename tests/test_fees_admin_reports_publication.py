"""Actual Fees administrative corpora plus input-preserving publication failures."""
import unittest
from publication_cli_support import PublicationCase

class FeesAdminReportsPublicationTests(PublicationCase, unittest.TestCase):
 NAMES=('fees_admin_differential','fees_admin_transfer_differential','fees_config_differential')
 DATA=('evidence/upstream/pump_fees.json','evidence/original/pump_fees/deployed.so')
 HELPERS={'fees_admin_differential':(), 'fees_config_differential':('fees_admin_differential','fee_recovery_fixture'), 'fees_admin_transfer_differential':('fees_admin_differential','fees_config_differential','fee_recovery_fixture')}
 PROGRAM='evidence/original/pump_fees/deployed.so'
 EXPECTED={'fees_admin_differential':444,'fees_admin_transfer_differential':56,'fees_config_differential':625}

if __name__=='__main__':unittest.main()
