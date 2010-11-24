from __future__ import with_statement

from os.path import isfile, dirname, join
import inspect

__all__ = ('DevRole', 'DeploymentRole')


class BaseRole(object):
    def __init__(self, hostname):
        self.hostname = hostname

        self.base_module = None
        self.dev_template_module = None

    def hostname_matches(self, full_hostname):
        if self.hostname in full_hostname:
            return True

        return False

    def get_module(self):
        raise NotImplemented()

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, self.hostname,)


class DevRole(BaseRole):
    local_name = 'settingslocal.py'
    local_module = 'settingslocal'

    empty_local_settings = \
        "# Override specific settings for this development machine here"

    def _create_local_settings(self, local_settings_path, template_module):
        if template_module:
            source = inspect.getsource(template_module)
        else:
            source = self.empty_local_settings
        
        with open(local_settings_path, 'w') as l:
            l.write(source)

    def get_module(self):
        local_settings_path = join(dirname(self.base_module.__file__), self.local_name)

        if not isfile(local_settings_path):
            self._create_local_settings(local_settings_path, self.dev_template_module)

        project = '.'.join(self.base_module.__name__.split('.')[0:-1])

        modulename = self.local_module
        if project:
            modulename = '%s.%s' % (project, self.local_module)

        module = __import__(modulename,
            globals(), locals(), ['*'])

        return module


class DeploymentRole(BaseRole):
    def __init__(self, hostname, module):
        super(DeploymentRole, self).__init__(hostname)
        self.module = module

    def get_module(self):
        return self.module
