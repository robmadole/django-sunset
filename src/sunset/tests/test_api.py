from __future__ import with_statement

import os
import shutil
import unittest
import textwrap

from sunset.api import _reset, BaseSettingsMissing, RolesNoMatch, hostname_like
from sunset.roles import BaseRole

# Backward compatible unittest
try:
    import unittest
    # skip was added in 2.7/3.1
    assert unittest.skip
except AttributeError:
    import unittest2 as unittest

STANDARD_SETTINGS = ['TEMPLATE_DIRS', 'USE_L10N', 'MANAGERS', 'MEDIA_ROOT',
                     'SITE_ID', 'DATABASES', 'MIDDLEWARE_CLASSES',
                     'ADMIN_MEDIA_PREFIX', 'TEMPLATE_LOADERS',
                     'ROOT_URLCONF', 'ADMINS', 'TEMPLATE_DEBUG',
                     'LANGUAGE_CODE', 'DEBUG', 'TIME_ZONE', 'SECRET_KEY',
                     'MEDIA_URL', 'USE_I18N', 'INSTALLED_APPS']


class ApiTest(unittest.TestCase):
    temporary_projects = []

    def setUp(self):
        _reset()
        self.project_path, self.settingsfunc = self.create_django_project()

    def tearDown(self):
        shutil.rmtree(self.project_path)

    def hostname(self):
        return os.uname()[1]

    def create_django_project(self):
        project_name = self.id().split('.')[-1]
        fixtures = os.path.join(os.path.dirname(__file__), 'fixtures')
        working = os.path.join(os.path.dirname(__file__), 'working')
        tpl_project = os.path.join(fixtures, 'tpl_project')
        project = os.path.join(working, project_name)

        if os.path.isdir(project):
            # Perhaps a bad test run left this
            shutil.rmtree(project)

        shutil.copytree(tpl_project, project)

        def get_settings():
            settings_module = __import__(
                'sunset.tests.working.%s.settings' % project_name,
                 globals(), locals(), ['*'])
            plain_settings = {}
            for setting in dir(settings_module):
                if setting == setting.upper():
                    plain_settings[setting] = getattr(settings_module, setting)
            return plain_settings

        return project, get_settings

    def make_settings(self, source):
        with open(os.path.join(self.project_path, 'settings.py'), 'w') as fh:
            fh.write(source)

    @property
    def current_settings(self):
        return self.settingsfunc()

    def assertStandardSettings(self, settings):
        for s in STANDARD_SETTINGS:
            self.assertTrue(s in settings)

    def test_can_read_base_settings(self):
        self.make_settings(textwrap.dedent("""
            from sunset import api

            import settingsbase
            api.collect(settingsbase)

            from sunset.collection import *
            """))

        settings = self.current_settings

        self.assertStandardSettings(settings)

    def test_can_set_dev_settings(self):
        self.make_settings(textwrap.dedent("""
            from sunset import api

            import settingsbase
            import settingsdev

            api.collect(settingsbase)
            api.dev_template(settingsdev)

            from sunset.collection import *
            """))

        settings = self.current_settings

        # The settingslocal file should not be created until roles is
        # called
        self.assertFalse(os.path.isfile(os.path.join(
            self.project_path, 'settingslocal.py')))
        self.assertStandardSettings(settings)

    def test_cannot_set_dev_without_base(self):
        self.make_settings(textwrap.dedent("""
            from sunset import api

            import settingsdev

            api.dev_template(settingsdev)

            from sunset.collection import *
            """))

        with self.assertRaises(BaseSettingsMissing) as ec:
            settings = self.current_settings

    def test_base_roll_can_match_hostname(self):
        role1 = BaseRole('non-matching-hostname')

        self.assertFalse(role1.hostname_matches('hostname1.local'))

        role2 = BaseRole('hostname')

        self.assertTrue(role2.hostname_matches('hostname1.local'))
        self.assertTrue(role2.hostname_matches('hostname2.local'))

    def test_api_hostname_like(self):
        hostname = self.hostname()

        if len(hostname) < 3:
            # This hostname is too short to run this test, skip it
            return

        self.assertTrue(hostname_like(self.hostname()))
        self.assertTrue(hostname_like(
            self.hostname(), 'not-match', 'not-match-too'))
        self.assertTrue(hostname_like(self.hostname().upper()))
        self.assertTrue(hostname_like(self.hostname()[:3]))
        self.assertFalse(hostname_like('something-that-will-never-match'))

    def test_can_create_dev_settings(self):
        self.make_settings(textwrap.dedent("""
            from sunset import api

            import settingsbase
            import settingsdev

            api.collect(settingsbase)
            api.dev_template(settingsdev)

            api.roles(
                api.dev('%s'))

            from sunset.collection import *
            """ % self.hostname()))

        settings = self.current_settings

        self.assertTrue(os.path.isfile(os.path.join(
            self.project_path, 'settingslocal.py')))
        self.assertStandardSettings(settings)

        self.assertTrue(settings['SETTINGS_LOCAL'])

    def test_can_create_deployment_settings(self):
        self.make_settings(textwrap.dedent("""
            from sunset import api

            import settingsbase
            import settingsdev

            from deployments import web01

            api.collect(settingsbase)
            api.dev_template(settingsdev)

            api.roles(
                api.deployment('%s', web01))

            from sunset.collection import *
            """ % self.hostname()))

        settings = self.current_settings

        # Should not have local settings
        self.assertFalse(os.path.isfile(os.path.join(
            self.project_path, 'settingslocal.py')))
        self.assertStandardSettings(settings)

        self.assertTrue(settings['SETTINGS_WEB_01'])

    def test_deployment_settings_missing_module(self):
        self.make_settings(textwrap.dedent("""
            from sunset import api

            import settingsbase
            import settingsdev

            api.collect(settingsbase)
            api.dev_template(settingsdev)

            api.roles(
                api.deployment('%s'))

            from sunset.collection import *
            """ % self.hostname()))

        with self.assertRaises(TypeError) as ec:
            settings = self.current_settings

    def test_can_add_settings_to_all(self):
        self.make_settings(textwrap.dedent("""
            from sunset import api

            import settingsbase
            import settingsdev

            from deployments import web01
            from deployments import facebook

            api.collect(settingsbase)
            api.collect(facebook)

            api.dev_template(settingsdev)

            api.roles(
                api.deployment('%s', web01), ignore_missing=False)

            from sunset.collection import *
            """ % self.hostname()))

        settings = self.current_settings

        # None of the hostname matched, so we should not have this setting
        self.assertFalse('FACEBOOK_KEY' in settings)

    def test_roles_do_not_match(self):
        self.make_settings(textwrap.dedent("""
            from sunset import api

            import settingsbase
            import settingsdev

            api.collect(settingsbase)
            api.dev_template(settingsdev)

            roles = (
                api.dev('hostname1-no-match'),
                api.dev('hostname2-no-match'),
                api.dev('hostname3-no-match'),
                api.dev('hostname4-no-match'))

            api.roles(*roles)

            from sunset.collection import *
            """))

        with self.assertRaises(RolesNoMatch) as ec:
            settings = self.current_settings

    def test_roles_do_not_match_but_ignored(self):
        self.make_settings(textwrap.dedent("""
            from sunset import api

            import settingsbase
            import settingsdev

            from deployments import cloud

            api.collect(settingsbase)
            api.collect(cloud)

            api.dev_template(settingsdev)

            api.roles(
                api.dev('hostname1-no-match'),
                api.dev('hostname2-no-match'),
                ignore_missing=True)

            from sunset.collection import *
            """))

        settings = self.current_settings

        self.assertTrue('CLOUD_DEPLOY' in settings)
        self.assertTrue(settings['CLOUD_DEPLOY'])

    def test_will_create_empty_settingslocal(self):
        self.make_settings(textwrap.dedent("""
            from sunset import api

            import settingsbase

            api.collect(settingsbase)

            api.roles(
                api.dev('%s'))

            from sunset.collection import *
            """ % self.hostname()))

        settings = self.current_settings

        settingslocal_path = os.path.join(
            self.project_path, 'settingslocal.py')

        with open(settingslocal_path) as fh:
            source = fh.read()

        self.assertEquals(
            "# Override specific settings for this development machine here",
            source)
