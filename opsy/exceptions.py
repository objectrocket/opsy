

class OpsyError(Exception):
    """Base class for exceptions in this module."""
    pass


class NoConfigFile(OpsyError):
    """Config file not found."""
    pass


class NoConfigSection(OpsyError):
    """Config section not found."""
    pass
