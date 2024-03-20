"""Mixin classes to reduce test code duplication."""

import logging
from abc import ABC, abstractmethod
from argparse import Namespace

import pytest
import requests_mock

from qpc.clicommand import CliCommand
from qpc.utils import get_server_location


class BulkClearTestsMixin(ABC):
    """
    Test the "clear" subcommand that uses bulk delete APIs.

    Other test classes that use this mixin need to define the properties below
    to customize the behaviors and expectations of these test methods.
    """

    command: CliCommand  # typically set in our test classes' setup_class

    @property
    @abstractmethod
    def _uri_object_root(self) -> str:
        """Root URI of the object (e.g. "/api/v1/scans/")."""

    @property
    @abstractmethod
    def _uri_bulk_delete(self) -> str:
        """Bulk delete URI (e.g. "/api/v1/scans/bulk_delete/")."""

    @property
    @abstractmethod
    def _message_clear_all_summary(self) -> str:
        """Message to display when "clear all" command completes."""

    @property
    @abstractmethod
    def _message_clear_all_skipped(self) -> str | None:
        """Message to display when "clear all" shows a skipped delete."""

    @property
    @abstractmethod
    def _message_no_objects_to_remove(self) -> str:
        """Message to display when no objects exist to remove."""

    @property
    @abstractmethod
    def _bulk_delete_name(self) -> str:
        """Name of object type as used in bulk delete API response."""

    @property
    @abstractmethod
    def _bulk_delete_skipped_because_name(self) -> str | None:
        """
        Name of related type that could cause an object to be skipped.

        If None, then tests assume that objects cannot be skipped in bulk delete.
        """

    def test_clear_all_empty(self, caplog):
        """Testing the "clear" command successfully with an empty list of objects."""
        get_url = get_server_location() + self._uri_object_root
        expected_error = self._message_no_objects_to_remove
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json={"count": 0})
            args = Namespace(name=None)
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert expected_error in caplog.text

    def test_clear_all_but_unexpected_error_in_initial_get(self, caplog, faker):
        """Test "clear all" when the GET fails unexpectedly before the delete POST."""
        get_url = get_server_location() + self._uri_object_root
        server_error_message = faker.sentence()
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=500, json=server_error_message)
            args = Namespace(name=None)
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            assert server_error_message in caplog.text

    def test_clear_all(self, caplog, faker):
        """Test "clear all" when all objects are successfully deleted."""
        get_url = get_server_location() + self._uri_object_root
        delete_url = get_server_location() + self._uri_bulk_delete

        all_ids = [faker.random_int() for _ in range(faker.random_int(min=5, max=15))]
        get_response = {"count": len(all_ids)}
        bulk_delete_response = {"deleted": all_ids}
        expected_response_message_parameters = {"deleted_count": len(all_ids)}

        if self._bulk_delete_skipped_because_name:
            expected_response_message_parameters["skipped_count"] = 0

        expected_message = (
            self._message_clear_all_summary % expected_response_message_parameters
        )

        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=get_response)
            mocker.post(delete_url, status_code=200, json=bulk_delete_response)
            args = Namespace(name=None)
            with caplog.at_level(logging.INFO):
                self.command.main(args)
                assert expected_message in caplog.text

    def test_clear_all_but_some_are_skipped(self, faker, caplog):
        """Test "clear all" when some objects are not deleted."""
        if not self._bulk_delete_skipped_because_name:
            pytest.skip("skipping is not relevant for this api")

        get_url = get_server_location() + self._uri_object_root
        delete_url = get_server_location() + self._uri_bulk_delete
        all_ids = [faker.random_int() for _ in range(faker.random_int(min=5, max=15))]
        get_response = {"count": len(all_ids)}

        skipped = [
            {
                self._bulk_delete_name: object_id,
                f"{self._bulk_delete_skipped_because_name}s": [faker.random_int()],
            }
            for object_id in faker.random_sample(all_ids)
        ]
        deleted = list(
            set(all_ids)
            - set(
                [skipped_object[self._bulk_delete_name] for skipped_object in skipped]
            )
        )
        bulk_delete_response = {"deleted": deleted, "skipped": skipped}
        with requests_mock.Mocker() as mocker:
            mocker.get(get_url, status_code=200, json=get_response)
            mocker.post(delete_url, status_code=200, json=bulk_delete_response)
            args = Namespace(name=None)
            with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
                self.command.main(args)
            for skipped_object in skipped:
                assert self._message_clear_all_skipped % {
                    f"{self._bulk_delete_name}_id": skipped_object[
                        self._bulk_delete_name
                    ],
                    f"{self._bulk_delete_skipped_because_name}_ids": skipped_object[
                        f"{self._bulk_delete_skipped_because_name}s"
                    ],
                }
            expected_message = self._message_clear_all_summary % {
                "deleted_count": len(deleted),
                "skipped_count": len(skipped),
            }
            assert expected_message in caplog.text
