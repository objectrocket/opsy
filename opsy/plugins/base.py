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
    def register_scheduler_jobs(self, app, run_once=False):
        """Register any scheduler jobs for the plugin.

        :param app: Flask app object
        :type app: Flask
        :param run_once: Control if the jobs are scheduled once
        :type run_once: bool
        """

    @abc.abstractmethod
    def register_cli_commands(self, cli):
        """Register any cli commands for the plugin."""

    @abc.abstractmethod
    def register_shell_context(self, shell_ctx):
        """Register any objects for the plugin on the shell context.

        :param shell_ctx: Shell variables dict
        :type shell_ctx: Dict
        """
