from google.appengine.dist import use_library
use_library('django', '1.2')

import os
from gaesessions import SessionMiddleware

COOKIE_KEY = "\x9f\x18\xef\x8e\x05\x14,M\x8f\xf2U\xb5\xe7\x11\xc0\x84\xc7\xecQY3\x19\xfb7S\xe5a\xb73.\xe8B\xf5\xa2\xfbW\xa4\x12\xfe)\xe5|\xa6\xbe\xa5E\xf9\xf7\xe8\x93b7\xd8\xed\xedC\xf9\xfe\xebs{\xef\xcbj"


def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    app = SessionMiddleware(app, cookie_key=COOKIE_KEY)
    return app
