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

        # terminate all sessions
        session.terminate()

        authorized_tokens = twitter.get_authorized_tokens()
        session['authorized_tokens'] = authorized_tokens

        twitter_id = authorized_tokens['user_id']
        username = authorized_tokens['screen_name']
        oauth_token = authorized_tokens['oauth_token']
        oauth_token_secret = authorized_tokens['oauth_token_secret']

        #for k,v in authorized_tokens.items():
        #    print k, v
        
        user = User.get_or_insert(twitter_id, twitter_id=long(twitter_id))

        # always keep the latest
        user.username = username
        user.oauth_token = oauth_token
        user.oauth_token_secret = oauth_token_secret
        user.put()

        template_values = {
            'temp': 'callback', #auth.request_token.key,
        }

        path = os.path.join(TEMPLATE, 'base.html')
        self.response.out.write(template.render(path, template_values))

        self.redirect('/timeline')


class TimelineApp(webapp.RequestHandler):

    def get(self):
        session = get_current_session()
        authorized_tokens = session.get('authorized_tokens', None)
        if authorized_tokens is None:
            self.redirect('/')

    	twitter = Twython(
    		twitter_token = CONSUMER_KEY,
    		twitter_secret = CONSUMER_SECRET,
    		oauth_token = authorized_tokens['oauth_token'],
    		oauth_token_secret = authorized_tokens['oauth_token_secret']
    	)

        temp = dict()
        page = 0
        total = 0
        while True:
            tweets = twitter.getFriendsTimeline(
                                             count=200,
                                             include_entities=1,
                                             page=page,
                                             #trim_user=1,
                                            )

            if len(tweets) == 0:
                break
            else:
                page = page + 1
                total = total + len(tweets)

            for tweet in tweets:
                user = tweet['user']['id']
                if not temp.has_key(user):
                    temp[user] = [tweet['user']['screen_name'], 0]

                count = temp[user][1]
                temp[user][1] = count + 1

        for k, v in temp.items():
            print k, v[0], v[1]

        print twitter.getRateLimitStatus()['remaining_hits']
        print total


application = webapp.WSGIApplication(
                [
                  ('/', HomeApp),
                  ('/callback', CallbackApp),
                  ('/timeline', TimelineApp),
                ],
                debug=DEBUG
              )

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
