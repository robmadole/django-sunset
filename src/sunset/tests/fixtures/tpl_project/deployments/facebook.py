from sunset.api import hostname_like

if hostname_like('development.local'):
    FACEBOOK_API_KEY = 'local'

if hostname_like('web01'):
    FACEBOOK_API_KEY = 'production'
