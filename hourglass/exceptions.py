

class HourglassError(Exception):
    """Base class for exceptions in this module."""

    pass


class NoConfigFile(HourglassError):
    """Config file not found."""

    pass
