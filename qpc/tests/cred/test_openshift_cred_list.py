"""Test openshift cred list in CLI."""

import json
import sys

import pytest

from qpc.cli import CLI
from qpc.cred import CREDENTIAL_URI, OPENSHIFT_CRED_TYPE
from qpc.utils import get_server_location


class TestOpenShiftListCredential:
    """Class for testing OpenShift list credential."""

    @pytest.mark.parametrize("ocp_cred_type", ("OPENSHIFT", "openshift", "OPENshift"))
    def test_list_filtered_cred_data(
        self,
        capsys,
        requests_mock,
        ocp_cred_type,
    ):
        """Test if cred list returns ocp creds."""
        url = get_server_location() + CREDENTIAL_URI
        openshift_cred_1 = {
            "id": 1,
            "name": "openshift_1",
            "cred_type": OPENSHIFT_CRED_TYPE,
        }
        openshift_cred_2 = {
            "id": 2,
            "name": "openshift_2",
            "cred_type": OPENSHIFT_CRED_TYPE,
        }
        results = [openshift_cred_1, openshift_cred_2]
        data = {"count": 2, "results": results}
        requests_mock.get(url, status_code=200, json=data)
        sys.argv = ["/bin/qpc", "cred", "list", "--type", ocp_cred_type]
        CLI().main()
        expected_dict = [
            {
                "cred_type": "openshift",
                "id": 1,
                "name": "openshift_1",
            },
            {
                "cred_type": "openshift",
                "id": 2,
                "name": "openshift_2",
            },
        ]
        out, err = capsys.readouterr()
        out_as_dict = json.loads(out)
        assert out_as_dict == expected_dict
        assert err == ""
