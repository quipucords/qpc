"""Test openshift source list in CLI."""
import json
import sys

from qpc.cli import CLI
from qpc.source import OPENSHIFT_SOURCE_TYPE, SOURCE_URI
from qpc.utils import get_server_location


class TestOpenShiftListSource:
    """Class for testing OpenShift list source."""

    def test_list_filtered_cred_data(
        self,
        capsys,
        requests_mock,
        ocp_credential_mock,
    ):
        """Test if source list returns ocp sources."""
        url = get_server_location() + SOURCE_URI
        ocp_source_1 = {
            "id": 1,
            "name": "ocp_source_1",
            "source_type": OPENSHIFT_SOURCE_TYPE,
            "credentials": [{"id": 1, "name": "ocp_cred_1"}],
            "hosts": ["1.2.3.4"],
        }
        ocp_source_2 = {
            "id": 2,
            "name": "ocp_source_2",
            "source_type": OPENSHIFT_SOURCE_TYPE,
            "credentials": [{"id": 1, "name": "ocp_cred_1"}],
            "hosts": ["4.3.2.1"],
            "port": 22,
        }
        results = [ocp_source_1, ocp_source_2]
        data = {"count": 2, "results": results}
        requests_mock.get(url, status_code=200, json=data)
        sys.argv = [
            "/bin/qpc",
            "source",
            "list",
            "--type",
            OPENSHIFT_SOURCE_TYPE,
        ]
        CLI().main()
        expected_dict = [
            {
                "id": 1,
                "name": "ocp_source_1",
                "source_type": OPENSHIFT_SOURCE_TYPE,
                "credentials": [{"id": 1, "name": "ocp_cred_1"}],
                "hosts": ["1.2.3.4"],
            },
            {
                "id": 2,
                "name": "ocp_source_2",
                "source_type": OPENSHIFT_SOURCE_TYPE,
                "credentials": [{"id": 1, "name": "ocp_cred_1"}],
                "hosts": ["4.3.2.1"],
                "port": 22,
            },
        ]
        out, err = capsys.readouterr()
        out_as_dict = json.loads(out)
        assert out_as_dict == expected_dict
        assert err == ""
