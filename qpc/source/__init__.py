"""Constants for the Sources commands."""

SUBCOMMAND = "source"
ADD = "add"
LIST = "list"
EDIT = "edit"
SHOW = "show"
CLEAR = "clear"

ANSIBLE_SOURCE_TYPE = "ansible"
NETWORK_SOURCE_TYPE = "network"
OPENSHIFT_SOURCE_TYPE = "openshift"
SATELLITE_SOURCE_TYPE = "satellite"
VCENTER_SOURCE_TYPE = "vcenter"

SOURCE_URI = "/api/v1/sources/"
SOURCE_TYPE_CHOICES = [
    ANSIBLE_SOURCE_TYPE,
    NETWORK_SOURCE_TYPE,
    OPENSHIFT_SOURCE_TYPE,
    SATELLITE_SOURCE_TYPE,
    VCENTER_SOURCE_TYPE,
]

BOOLEAN_CHOICES = ["True", "False", "true", "false"]
VALID_SSL_PROTOCOLS = ["SSLv23", "TLSv1", "TLSv1_1", "TLSv1_2"]
