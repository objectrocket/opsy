import abc
import six


@six.add_metaclass(abc.ABCMeta)
class BaseOpsyPlugin(object):
    """Base class for plugins."""

    def __init__(self, app):
        pass

    def _parse_config(self, app):
        """Perform any config parsing necessary for the plugin.

        :param app: Flask app object
        :type app: Flask
        :return: Flask app object
        :rtype: Flask
        """

    @abc.abstractmethod
    def register_blueprints(self, app):
        """Register any blueprints that the plugin provides.

        :param app: Flask app object
        :type app: Flask
        :return: Flask app object
        :rtype: Flask
        """

    @abc.abstractmethod
    def register_scheduler_jobs(self, app):
        """Register any scheduler jobs for the plugin.

        :param app: Flask app object
        :type app: Flask
        :return: List of apscheduler jobs
        :rtype: List
        """

    @abc.abstractmethod
    def register_cli_commands(self, app, cli):
        """Register any cli commands for the plugin.

        :param app: Flask app object
        :type app: Flask
        :return: List of cli commands
        :rtype: List
        """

    @property
    @abc.abstractmethod
    def shell_objects(self):
        """Returns a dict of objects to be included in the shell context.

        :return: Dict of objects
        :rtype: Dict
        """
