"""Constants for the Sources commands."""

SUBCOMMAND = "source"
ADD = "add"
LIST = "list"
EDIT = "edit"
SHOW = "show"
CLEAR = "clear"

NETWORK_SOURCE_TYPE = "network"
VCENTER_SOURCE_TYPE = "vcenter"
SATELLITE_SOURCE_TYPE = "satellite"
OPENSHIFT_SOURCE_TYPE = "openshift"

SOURCE_URI = "/api/v1/sources/"

BOOLEAN_CHOICES = ["True", "False", "true", "false"]
VALID_SSL_PROTOCOLS = ["SSLv23", "TLSv1", "TLSv1_1", "TLSv1_2"]
