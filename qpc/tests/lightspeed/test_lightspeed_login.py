"""Test the CLI module's Lightspeed Login command."""

import sys
from unittest import mock
from unittest.mock import MagicMock

import pytest

from qpc import messages
from qpc.cli import CLI
from qpc.lightspeed.auth import LightspeedAuth
from qpc.lightspeed.exceptions import LightspeedAuthError


class TestLightspeedLogin:
    """Class for testing Lightspeed login command."""

    def test_lightspeed_login_invalid_username_args_err(self, capsys):
        """Testing that lightspeed login rejects older username args."""
        test_argv = ["/bin/qpc", "lightspeed", "login", "--username", "invalid-user"]
        with pytest.raises(SystemExit), mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert "error: unrecognized arguments: --username invalid-user" in err

    def test_lightspeed_login_invalid_password_args_err(self, capsys):
        """Testing that lightspeed login rejects older password args."""
        test_argv = ["/bin/qpc", "lightspeed", "login", "--password"]
        with pytest.raises(SystemExit), mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        out, err = capsys.readouterr()
        assert out == ""
        assert "error: unrecognized arguments: --password" in err

    def test_lightspeed_login_normal_behavior(self, faker, mocker, capsys):
        """Testing that lightspeed login displays the expected messages."""
        auth_token = faker.md5()
        user_code = faker.slug()
        verification_uri_complete = faker.url()
        lightspeed_auth = MagicMock()
        lightspeed_auth.request_auth.return_value = {
            "user_code": user_code,
            "verification_uri_complete": verification_uri_complete,
        }
        lightspeed_auth.wait_for_authorization.return_value = auth_token
        mocker.patch.object(
            LightspeedAuth, "request_auth", return_value=lightspeed_auth
        )
        test_argv = ["/bin/qpc", "lightspeed", "login"]
        with mock.patch.object(sys, "argv", test_argv):
            CLI().main()
        out, err = capsys.readouterr()
        stdout_lines = out.splitlines()
        assert "Lightspeed login authorization requested" in stdout_lines[0]
        assert "User Code: " in stdout_lines[1]
        assert "Authorization URL: " in stdout_lines[2]
        assert "Waiting for login authorization ..." in stdout_lines[3]
        assert "Login authorization successful." in stdout_lines[4]

    def test_lightspeed_login_auth_error(self, mocker, capsys):
        """Testing that lightspeed login catches auth errors."""
        err_message = messages.LIGHTSPEED_LOGIN_REQUEST_FAILED % "Network Error"
        mocker.patch.object(
            LightspeedAuth, "request_auth", side_effect=LightspeedAuthError(err_message)
        )
        test_argv = ["/bin/qpc", "lightspeed", "login"]
        with mock.patch.object(sys, "argv", test_argv), pytest.raises(SystemExit):
            CLI().main()
        out, err = capsys.readouterr()
        assert err_message in err
