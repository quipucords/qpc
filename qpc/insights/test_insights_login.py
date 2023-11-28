"""Test the CLI module's Insights Login command."""

import sys
from unittest import mock
from unittest.mock import MagicMock

import pytest

from qpc import messages
from qpc.cli import CLI
from qpc.insights.auth import InsightsAuth
from qpc.insights.exceptions import InsightsAuthError


class TestInsightsLogin:
    """Class for testing insights login command."""

    def test_insights_login_invalid_username_args_err(self, capsys):
        """Testing that insights login rejects older username args."""
        test_argv = ["/bin/qpc", "insights", "login", "--username", "invalid-user"]
        with pytest.raises(SystemExit), mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert "error: unrecognized arguments: --username invalid-user" in err

    def test_insights_login_invalid_password_args_err(self, capsys):
        """Testing that insights login rejects older password args."""
        test_argv = ["/bin/qpc", "insights", "login", "--password"]
        with pytest.raises(SystemExit), mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert "error: unrecognized arguments: --password" in err

    def test_insights_login_normal_behavior(self, faker, mocker, capsys):
        """Testing that insights login displays the expected messages."""
        auth_token = faker.md5()
        user_code = faker.slug()
        verification_uri_complete = faker.url()
        insights_auth = MagicMock()
        insights_auth.request_auth.return_value = {
            "user_code": user_code,
            "verification_uri_complete": verification_uri_complete,
        }
        insights_auth.wait_for_authorization.return_value = auth_token
        mocker.patch.object(InsightsAuth, "request_auth", return_value=insights_auth)
        test_argv = ["/bin/qpc", "insights", "login"]
        with mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        out, err = capsys.readouterr()
        stdout_lines = out.splitlines()
        assert "Insights login authorization requested" in stdout_lines[0]
        assert "User Code: " in stdout_lines[1]
        assert "Authorization URL: " in stdout_lines[2]
        assert "Waiting for login authorization ..." in stdout_lines[3]
        assert "Login authorization successful." in stdout_lines[4]

    def test_insights_login_auth_error(self, faker, mocker, capsys):
        """Testing that insights login catches auth errors."""
        err_message = messages.INSIGHTS_LOGIN_REQUEST_FAILED % "Network Error"
        mocker.patch.object(
            InsightsAuth, "request_auth", side_effect=InsightsAuthError(err_message)
        )
        test_argv = ["/bin/qpc", "insights", "login"]
        with mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        out, err = capsys.readouterr()
        assert err_message in err
