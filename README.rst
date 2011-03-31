django-sunset
=============

Django Sunset makes working with Django settings in a team environment or a
multi-server deployment a bit easier.

The basic idea is that you separate your settings modules and based on the
**hostname** of the machine you are running on, do the appropriate thing.

Installation
------------

Using Pip:

::

    pip install django-sunset

Or ``easy_install`` if you don't have Pip:

::

    easy_install django-sunset

Basic Usage
-----------

When you create a new project in Django a Python module called ``settings`` (a
file called ``settings.py``) holds all the configuration for how your project
will operate.

If you are new to Django, `this tutorial
<http://docs.djangoproject.com/en/dev/intro/tutorial01/>`_ can get you started.

Start with a new project (``django-admin.py startproject mysite``)::

    mysite/
        __init__.py
        manage.py
        settings.py
        urls.py


Rename the ``settings.py`` file to ``settingsbase.py`` ::

    mysite/
        __init__.py
        manage.py
        settingsbase.py
        urls.py

Let's find out what your current hostname is ::

    $ python -c 'import os; print os.uname()[1]'
    rob-madoles-macbook-pro.local

Mine is ``rob-madoles-macbook-pro.local``.  Throughout the examples I'll use
this, substitute your own where appropriate.

Now create ``settings.py`` with the following contents ::

    from sunset import api

    import settingsbase
    api.collect(settingsbase)

    api.roles(
        api.dev('rob-madoles-macbook-pro'))

    from sunset.collection import *

We should have this ::

    mysite/
        __init__.py
        manage.py
        settings.py
        settingsbase.py
        urls.py

Kick Django off something like this ::

    $ ./manage.py shell
    Python 2.7 (r27:82500, Aug 16 2010, 15:13:20)
    [GCC 4.2.1 (Apple Inc. build 5664)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)
    >>>

Look again and you should see a ``settingslocal.py``.  It's empty but a comment
at the top to indicate you place your local settings here. ::

    mysite/
        __init__.py
        manage.py
        settings.py
        settingsbase.py
        settingslocal.py
        urls.py

Since these settings are local to only your machine, you probably don't want
them in the repository.  Add it to ``.gitignore`` or ``.hgignore`` or whatever
equivalent ignore file you have.

Go ahead and make some changes in there, how about we change the database?

Edit ``settingslocal.py`` ::

    DEBUG = True

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'database.db',
        }
    }

Run the Django shell again and inspect the value ::

    $ ./manage.py shell
    Python 2.7 (r27:82500, Aug 16 2010, 15:13:20)
    [GCC 4.2.1 (Apple Inc. build 5664)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)
    >>> from django.conf import settings
    >>> print settings.DATABASES['default']['ENGINE']
    django.db.backends.sqlite3
    >>> print settings.DATABASES['default']['NAME']
    database.db

Great, you have local settings now and you don't have to touch the main
``settings.py`` file.

Base your local settings on a template
--------------------------------------

Let's take what we have in the previous example and expand a bit on it.  For our
team we have quite a few settings and a template would be nicer to start with
instead of an empty file.

Edit ``settings.py`` with the following contents ::

    from sunset import api

    import settingsbase
    api.collect(settingsbase)

    import settingsdev
    api.dev_template(settingsdev)

    api.roles(
        api.dev('rob-madoles-macbook-pro'))

    from sunset.collection import *

We are adding this ::

    import settingsdev
    api.dev_template(settingsdev)

Create an empty file called ``settingsdev.py`` ::

    touch settingsdev.py

Make the contents of ``settingsdev.py`` to this ::

    DEBUG = True

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'database.db',
        }
    }

    FACEBOOK_APP_ID = ''
    FACEBOOK_APP_SECRET = ''
    FACEBOOK_API_KEY = ''

That works better, each developer will not have to repeat the same typing.

Remove your ``settingslocal.py`` so Django Sunset can recreate it for you.
::

    rm settingslocal.py

And again load up the Django shell ::

    $ ./manage.py shell
    Python 2.7 (r27:82500, Aug 16 2010, 15:13:20)
    [GCC 4.2.1 (Apple Inc. build 5664)] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    (InteractiveConsole)

If you look at ``settingslocal.py`` now you'll see the extra goodies.

Settings for deployment or production
-------------------------------------

Settings for developers are one thing, they change often and are not usually
tracked in a VCS.

Servers are a different story.  You usually control these pretty closely and
change them seldom once they are running.

So for deployments the syntax is a bit different.

Create a directory called ``deployments``  and a file called ``web01.py`` ::

    mkdir deployments
    touch deployments/__init__.py
    touch deploymnets/web01.py

Edit ``settings.py`` with the following contents ::

    from sunset import api

    import settingsbase
    api.collect(settingsbase)

    import settingsdev
    api.dev_template(settingsdev)

    from deployments import web01

    api.roles(
        api.dev('rob-madoles-macbook-pro')
        api.deployment('web01', web01)
        )

    from sunset.collection import *

Notice that the ``api.deployment`` constructor takes 2 arguments.  The first is
the partial hostname, the second is the module that will be added to the
collection of settings if the hostname matches.

Now you can edit the ``web01.py`` file and change whatever settings you like.

As a bonus, it's easy to impersonate a deployed server locally.  Simply set your
hostname as a deployment.

::

    api.roles(
        #api.dev('rob-madoles-macbook-pro')
        api.deployment('rob-madoles-macbook-pro', web01)
        api.deployment('web01', web01)
        )


In the case that you have a deployment to the cloud and do not know the hostname
that you code will be sitting in you can simply set the ignore_missing flag.

::

    from sunset import api

    import settingsbase
    api.collect(settingsbase)

    import settingsdev
    api.dev_template(settingsdev)

    from deployments import web01
    from delpoyments import cloud

    api.collect(cloud)

    api.roles(
        api.dev('rob-madoles-macbook-pro'),
        api.deployment('web01', web01),
        ignore_missing=True)

    from sunset.collection import *

Using one module for a group of settings
----------------------------------------

With Django Sunset you can separate your settings by hostname but there are
still situations where this isn't always the best method.

For example, let's say one developer is responsible for setting up the Facebook
API keys for the team.  She's gone into Facebook and spent the last half-hour
making Applications and editing configurations.

Instead of emailing everyone their keys, app id's and secrets she can create one
module that houses them all.

Edit ``settings.py`` with the following contents ::

    from sunset import api

    import settingsbase
    api.collect(settingsbase)

    import settingsdev
    api.collect(settingsdev)

    from deployments import web01

    from deployments import facebook
    api.collect(facebook)

    api.roles(
        api.dev('rob-madoles-macbook-pro')
        api.deployment('web01', web01)
        )

    from sunset.collection import *

What we've added here is ::

    from deployments import facebook
    api.collect(facebook)

Now let's create ``deployments/facebook.py`` with the following contents ::

    from sunset.api import hostname_like

    if hostname_like('rob-madoles-macbook-pro'):
        FACEBOOK_APP_ID = '13782914721428'
        FACEBOOK_APP_SECRET = 'asdfh8a7f8f2238a8s7d68f72'
        FACEBOOK_API_KEY = '8a7f79829f6a6ft0aygafkgsdaf86t4ugyagtf8'

    if hostname_like('ted-jones-macbook-pro'):
        FACEBOOK_APP_ID = '8723849237428'
        FACEBOOK_APP_SECRET = '8ffa23jk4fa9f34af3498afhf4'
        FACEBOOK_API_KEY = '123h129318hf91uwhd1937g8163g817317gd817'

    if hostname_like('web01', 'web02', 'web03'):
        FACEBOOK_APP_ID = '8723849237428'
        FACEBOOK_APP_SECRET = '8ffa23jk4fa9f34af3498afhf4'
        FACEBOOK_API_KEY = '123h129318hf91uwhd1937g8163g817317gd817'

So now this module performs the hostname matching internally instead of relying
on the roles.  Also notice how ``hostname_like`` can take multiple arguments
where if any of the hostnames match the settings will be applied.

The developer still has the opportunity to override the settings from the
``facebook`` module in their own ``settingslocal``.  The order in which API
calls happen within the ``settings`` module is preserved.

Questions and issues
--------------------

Please enter issues in `GitHub <https://github.com/robmadole/django-sunset/issues>`_ or you can email me directory robmadole@gmail.com.
