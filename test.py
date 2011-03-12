from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext.webapp.util import run_wsgi_app

import tweepy
from settings import *


class HomeApp(webapp.RequestHandler):

    def get(self):

        #public_tweets = tweepy.api.public_timeline()
        #for tweet in public_tweets:
        #    print tweet.text

        callback_url = 'http://localhost:8080/'
        auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET, 
                                   callback_url)

        try:
            self.redirect(auth.get_authorization_url())
        except tweepy.TweepError, e:
            print e
            print 'error! failed to get request token'
            return

        template_values = {
            'temp': auth.request_token.key,
        }

        path = os.path.join(TEMPLATE, 'base.html')
        self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
                [
                  ('/', HomeApp),
                ],
                debug=DEBUG
              )

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
