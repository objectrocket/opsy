

class OpsyError(Exception):
    """Base class for exceptions in opsy."""


class NoConfigFile(OpsyError):
    """Config file not found."""


class NoConfigSection(OpsyError):
    """Config section not found."""


class MissingConfigOption(OpsyError):
    """Missing a required option in the config file."""


class DuplicateError(OpsyError):
    """Resource with this attribute already exists."""
