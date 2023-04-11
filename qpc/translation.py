"""Translation initalization utility."""


import gettext

T = gettext.translation("qpc", "locale", fallback=True)

if hasattr(T, "ugettext"):
    # pylint: disable=no-member
    _ = T.ugettext
else:
    _ = T.gettext
