from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext.webapp.util import run_wsgi_app

from gaesessions import get_current_session
from twython import Twython

from models import User
from settings import *


class HomeApp(webapp.RequestHandler):

    def get(self):
        session = get_current_session()

        twitter = Twython(
            twitter_token = CONSUMER_KEY,
            twitter_secret = CONSUMER_SECRET,
            callback_url = 'http://localhost:8080/callback',
        )

        auth_props = twitter.get_authentication_tokens()
        session['auth_props'] = auth_props

        self.redirect(auth_props['auth_url'])

        template_values = {
            'temp': 'home', #auth.request_token.key,
        }

        path = os.path.join(TEMPLATE, 'base.html')
        self.response.out.write(template.render(path, template_values))


class CallbackApp(webapp.RequestHandler):

    def get(self):
        session = get_current_session()
        auth_props = session.get('auth_props')

    	twitter = Twython(
    		twitter_token = CONSUMER_KEY,
    		twitter_secret = CONSUMER_SECRET,
    		oauth_token = auth_props['oauth_token'],
    		oauth_token_secret = auth_props['oauth_token_secret']
    	)

        authorized_tokens = twitter.get_authorized_tokens()
        twitter_id = authorized_tokens['user_id']
        username = authorized_tokens['screen_name']
        oauth_token = authorized_tokens['oauth_token']
        oauth_token_secret = authorized_tokens['oauth_token_secret']

        #for k,v in authorized_tokens.items():
        #    print k, v
        
        user = User.get_or_insert(twitter_id, 
                                  twitter_id=long(twitter_id),
                                  username=username,
                                  oauth_token=oauth_token,
                                  oauth_token_secret=oauth_token_secret)

        template_values = {
            'temp': 'callback', #auth.request_token.key,
        }

        path = os.path.join(TEMPLATE, 'base.html')
        self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
                [
                  ('/', HomeApp),
                  ('/callback', CallbackApp),
                ],
                debug=DEBUG
              )

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
