"""Test the utils module."""

from qpc import utils


class TestUtils:
    """Class for testing the utils module qpc."""

    def test_read_client_token(self):
        """Testing the read client token function."""
        check_value = False
        if not utils.QPC_CLIENT_TOKEN.exists():
            check_value = True
            expected_token = "100"
            token_json = {utils.CLIENT_TOKEN_KEY: expected_token}
            utils.write_client_token(token_json)
        token = utils.read_client_token()
        assert isinstance(token, str)
        if check_value:
            assert token == expected_token

    def test_extract_json_from_tarfile(self):
        """Test extracting json from tarfile."""
        report_json = {
            "report_id": 1,
            "report_type": "deployments",
            "report_version": "0.9.0.1b025b8",
            "status": "completed",
            "report_platform_id": "5f2cc1fd-ec66-4c67-be1b-171a595ce319",
            "system_fingerprints": [{"bios_uuid": "value"}],
        }
        test_file = {"test.json": report_json}
        fileobj = utils.create_tar_buffer(test_file)
        json = utils.extract_json_from_tar(fileobj, print_pretty=False)
        assert json == report_json

    def test_tabular_format(self):
        """Test tabular output from json_data."""
        json_data = []
        output = utils.tabular_format(json_data, {})
        assert output == "No data to display."
        json_data = [
            {
                "id": "1",
                "name": "scan1",
                "most_recent": {"report_id": "1", "status": "completed"},
            },
            {
                "id": "2",
                "name": "scan1",
                "most_recent": {"report_id": "2", "status": "completed"},
            },
            {"id": "3", "name": "scan3"},
        ]
        fields = {
            "scan_id": "id",
            "scan_name": "name",
            "report_id": "most_recent.report_id",
            "status": "most_recent.status",
        }
        output = utils.tabular_format(json_data, fields)
        output = output.split("\n")
        # Test table headers
        for field in fields.keys():
            assert field in output[0]
        # Test the presence of data in rows
        for index, data in enumerate(json_data):
            for path in fields.values():
                value = utils.json_data_deep_get(data, path)
                assert str(value) in output[index + 2]
