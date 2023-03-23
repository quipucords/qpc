"""Test the CLI module."""

import unittest

from qpc.scan import JBOSS_BRMS, JBOSS_EAP, JBOSS_FUSE, JBOSS_WS
from qpc.scan.utils import get_enabled_products, get_optional_products


class ScanUtilsTests(unittest.TestCase):
    """Class for testing the scan utils."""

    def test_default_optional_values(self):
        """Testing the scan default optional product values."""
        disabled_default = {
            JBOSS_FUSE: False,
            JBOSS_EAP: False,
            JBOSS_BRMS: False,
            JBOSS_WS: False,
        }
        result = get_optional_products([])
        self.assertEqual(disabled_default, result)

    def test_default_extended_search_values(self):
        """Testing the scan default extended searchvalues."""
        disabled_default = {
            JBOSS_FUSE: False,
            JBOSS_EAP: False,
            JBOSS_BRMS: False,
            JBOSS_WS: False,
            "search_directories": [],
        }
        result = get_enabled_products([], [], True)
        self.assertEqual(disabled_default, result)
