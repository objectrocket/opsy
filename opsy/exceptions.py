

class OpsyError(Exception):
    """Base class for exceptions in opsy."""

    pass


class NoConfigFile(OpsyError):
    """Config file not found."""

    pass


class NoConfigSection(OpsyError):
    """Config section not found."""

    pass


class DuplicateName(OpsyError):
    """Resource with this name already exists."""

    pass
