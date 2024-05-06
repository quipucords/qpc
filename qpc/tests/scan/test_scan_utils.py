"""Test the CLI module."""

from qpc.scan import JBOSS_EAP, JBOSS_FUSE, JBOSS_WS
from qpc.scan.utils import get_enabled_products, get_optional_products


class TestScanUtils:
    """Class for testing the scan utils."""

    def test_default_optional_values(self):
        """Testing the scan default optional product values."""
        disabled_default = {
            JBOSS_FUSE: False,
            JBOSS_EAP: False,
            JBOSS_WS: False,
        }
        result = get_optional_products([])
        assert disabled_default == result

    def test_default_extended_search_values(self):
        """Testing the scan default extended searchvalues."""
        disabled_default = {
            JBOSS_FUSE: False,
            JBOSS_EAP: False,
            JBOSS_WS: False,
            "search_directories": [],
        }
        result = get_enabled_products([], [], True)
        assert disabled_default == result
