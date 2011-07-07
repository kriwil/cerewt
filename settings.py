import os

PATH = os.path.dirname(__file__)
TEMPLATE = os.path.join(PATH, 'templates')
ADMIN_TEMPLATE = os.path.join(TEMPLATE, 'admin')

# twitter
CONSUMER_KEY = ''
CONSUMER_SECRET = ''

# kriwil
KRWL_OAUTH_TOKEN = ''
KRWL_OAUTH_TOKEN_SECRET = ''

DEBUG = True
MAX_TWEETS = 500

try:
    from local_settings import *
except ImportError:
    pass
