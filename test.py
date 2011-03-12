from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext.webapp.util import run_wsgi_app

#import tweepy
from twython import Twython
from settings import *


class HomeApp(webapp.RequestHandler):

    def get(self):

        #public_tweets = tweepy.api.public_timeline()
        #for tweet in public_tweets:
        #    print tweet.text

        #callback_url = 'http://localhost:8080/'
        #auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, 
        #                           callback_url)

        #try:
        #    self.redirect(auth.get_authorization_url())
        #except tweepy.TweepError, e:
        #    print e
        #    print 'error! failed to get request token'
        #    return

        twitter = Twython(
            twitter_token = CONSUMER_KEY,
            twitter_secret = CONSUMER_SECRET,
            callback_url = 'http://localhost:8080/callback',
        )

        auth_props = twitter.get_authentication_tokens()
        #self.redirect(auth_props['auth_url'])
        print '-----'
        print auth_props

        template_values = {
            'temp': 'home', #auth.request_token.key,
        }

        path = os.path.join(TEMPLATE, 'base.html')
        self.response.out.write(template.render(path, template_values))


class CallbackApp(webapp.RequestHandler):

    def get(self):

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
