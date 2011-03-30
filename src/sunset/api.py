import os

from sunset import collection
from sunset.roles import DevRole as dev
from sunset.roles import DeploymentRole as deployment

_base_module = None
_dev_template_module = None


def _reset():
    """
    Returns Django Sunset to an initial state, before anything has been done to
    it
    """
    global _base_module, _dev_template_module

    _base_module = None
    _dev_template_module = None

    for i in dir(collection):
        delattr(collection, i)


class BaseSettingsMissing(Exception):
    """
    For some operations, the base settings must be set first; raise this
    exception to indicate that the base settings are missing.
    """
    pass


class RolesNoMatch(Exception):
    """
    If no hostname could be found that matches the list of roles the user has
    defined, this should be raised
    """
    pass


def _extend_collection(module):
    """
    Takes the settings within the provided module and adds them to the
    collection that will eventually become the settings for this Django project
    """
    for setting in dir(module):
        if setting == setting.upper():
            setattr(collection, setting, getattr(module, setting))


def hostname_like(*hostnames):
    """
    Takes the cmp_hostname and determines if it matches the real hostname of
    this machine
    """
    for cmp_hostname in hostnames:
        real_hostname = os.uname()[1]
        if cmp_hostname.lower() in real_hostname.lower():
            return True
        return False


def collect(module):
    """
    Takes all the settings within the module and adds them to what will become
    the final settings for the Django project
    """
    global _base_module

    if not _base_module and 'SECRET_KEY' in dir(module):
        # Let's assume this is the base_module
        _base_module = module

    _extend_collection(module)


def dev_template(module):
    """
    Sunset supports the creation of a settingslocal.py file that is specific to
    the developer (that doesn't get checked into the code repository) and
    allows settings to be overridden.  The module argument here represents that
    settings template.
    """
    global _base_module, _dev_template_module

    if not _base_module:
        raise BaseSettingsMissing('Cannot set the development template '
            'module, the base has not been set yet')

    _dev_template_module = module


def roles(*roles, **kwargs):
    """
    Takes a list of roles and populates the collection according to which roles
    match the hostname.
    """
    global _base_module, _dev_template_module

    hostname = os.uname()[1]

    for node in roles:
        if node.hostname_matches(hostname):
            node.base_module = _base_module
            node.dev_template_module = _dev_template_module

            module = node.get_module()
            _extend_collection(module)

            return node

    # Getting to here means we did not match any hosts
    if not kwargs.get('ignore_missing', False):
        raise RolesNoMatch('We could not find any matches for hostname %s, you '
            'probably need to add this host into your settings' % hostname)
