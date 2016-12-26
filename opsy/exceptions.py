

class OpsyError(Exception):
    """Base class for exceptions in opsy."""

    pass


class NoConfigFile(OpsyError):
    """Config file not found."""

    pass


class NoConfigSection(OpsyError):
    """Config section not found."""

    pass


class MissingConfigOption(OpsyError):
    """Missing a required option in the config file."""

    pass


class DuplicateError(OpsyError):
    """Resource with this attribute already exists."""

    pass
