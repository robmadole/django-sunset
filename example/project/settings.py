from sunset import api

import settingsbase
api.collect(settingsbase) 

import settingsdev
api.dev_template(settingsdev)

# If you run the example, add your own hostname below.
# Find out with this command
#
#    python -c 'import os; print os.uname()[1]'

from deployments import web01

api.roles(
    api.dev('ADD YOUR HOSTNAME HERE'),
    api.dev('rob-madoles-macbook-pro'),
    api.deployment('web01', web01))

from sunset.collection import *
