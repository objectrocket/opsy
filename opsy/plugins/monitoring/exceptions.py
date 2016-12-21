from opsy.exceptions import OpsyError


class OpsyMonitoringError(OpsyError):
    """Base class for exceptions in the monitoring plugin."""


class PollFailure(OpsyMonitoringError):
    """The poll failed."""


class BackendNotFound(OpsyMonitoringError):
    """Unable to load specified backend."""


class DuplicateFilterEntity(OpsyMonitoringError):
    """Duplicate dashboard filter entity."""
