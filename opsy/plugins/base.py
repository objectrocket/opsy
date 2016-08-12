import abc
import six


@six.add_metaclass(abc.ABCMeta)
class BaseOpsyPlugin(object):
    '''Base class for plugins.'''

    def __init__(self, app):
        pass

    def _parse_config(self, app):
        '''Performs any config parsing necessary for the plugin.
        Should be called in the plugin's __init__(). Optional.

        :param app: Flask app object
        :type app: Flask
        :return: Flask app object
        :rtype: Flask
        '''

    @abc.abstractmethod
    def register_blueprints(self, app):
        '''Registers any blueprints that the plugin provides.

        :param app: Flask app object
        :type app: Flask
        :return: Flask app object
        :rtype: Flask
        '''

    @abc.abstractmethod
    def register_scheduler_jobs(self, app):
        '''Registers any scheduler jobs for the plugin.

        :param app: Flask app object
        :type app: Flask
        :return: List of apscheduler jobs
        :rtype: List of Jobs
        '''
