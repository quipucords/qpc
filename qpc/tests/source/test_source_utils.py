"""Test source utils."""

from types import SimpleNamespace

import pytest

from qpc.source.utils import build_source_payload


def make_args(overrides=None):
    """Create a SimpleNamespace args object with optional overrides."""
    base = {
        "name": "test-source",
        "type": "network",
        "hosts": ["host1"],
        "cred": ["cred1"],
        "credentials": [1],
    }
    if overrides:
        base |= overrides
    return SimpleNamespace(**base)


class TestBuildSourcePayloadV2:
    """Test build_source_payload with V2 field structure."""

    def test_only_required_fields(self):
        """Should build minimal payload with required fields only."""
        args = make_args()
        result = build_source_payload(args)
        assert result == {
            "name": "test-source",
            "source_type": "network",
            "hosts": ["host1"],
            "credentials": [1],
            "port": None,
            "proxy_url": None,
        }

    def test_add_none_false_omits_missing_fields(self):
        """Should omit missing fields when add_none is False."""
        args = make_args({"ssl_cert_verify": None, "port": None})
        result = build_source_payload(args, add_none=False)
        assert "ssl_cert_verify" not in result
        assert "port" not in result

    def test_full_payload_is_flat(self):
        """Should build a full payload with all supported fields at the top level."""
        args = make_args(
            {
                "exclude_hosts": ["host2"],
                "port": 443,
                "ssl_cert_verify": "true",
                "disable_ssl": "false",
                "ssl_protocol": "TLSv1_1",
                "use_paramiko": "true",
            }
        )
        result = build_source_payload(args)
        assert result == {
            "name": "test-source",
            "source_type": "network",
            "hosts": ["host1"],
            "exclude_hosts": ["host2"],
            "credentials": [1],
            "port": 443,
            "ssl_cert_verify": True,
            "disable_ssl": False,
            "ssl_protocol": "TLSv1_1",
            "use_paramiko": "true",
            "proxy_url": None,
        }

    @pytest.mark.parametrize(
        "ssl_val, expected",
        [("true", True), ("false", False)],
    )
    def test_ssl_cert_verify_boolean_parsing(self, ssl_val, expected):
        """Should convert ssl_cert_verify string to boolean."""
        args = make_args({"ssl_cert_verify": ssl_val})
        result = build_source_payload(args)
        assert result["ssl_cert_verify"] is expected

    @pytest.mark.parametrize(
        "disable_val, expected",
        [("true", True), ("false", False)],
    )
    def test_disable_ssl_boolean_parsing(self, disable_val, expected):
        """Should convert disable_ssl string to boolean."""
        args = make_args({"disable_ssl": disable_val})
        result = build_source_payload(args)
        assert result["disable_ssl"] is expected
