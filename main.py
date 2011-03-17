from datetime import datetime, timedelta

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext.webapp.util import run_wsgi_app

from gaesessions import get_current_session
from twython import Twython

import simplejson

from models import User, UserStatistic
from settings import *


class HomeApp(webapp.RequestHandler):

    def get(self):
        template_values = {
            'temp': 'home',
        }

        path = os.path.join(TEMPLATE, 'base.html')
        self.response.out.write(template.render(path, template_values))


class ConnectApp(webapp.RequestHandler):

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
            self.redirect('/connect')

    	twitter = Twython(
    		twitter_token = CONSUMER_KEY,
    		twitter_secret = CONSUMER_SECRET,
    		oauth_token = authorized_tokens['oauth_token'],
    		oauth_token_secret = authorized_tokens['oauth_token_secret']
    	)

        twitter_id = authorized_tokens['user_id']
        rate_limit = 0

        statistic = UserStatistic.get_by_key_name(twitter_id)
        if statistic is None:
            statistic = UserStatistic(
                                      key_name=twitter_id,
                                      twitter_id=long(twitter_id),
                                     )
            statistic.put()

        # Newly created
        stat = dict()
        total = 0

        if statistic.created == statistic.updated \
            or not statistic.statistics \
            or statistic.updated + timedelta(hours=1) < datetime.now():

            from_db = False
            page = 0
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
                    user = tweet['user']['screen_name']
                    if not stat.has_key(user):
                        stat[user] = 0

                    stat[user] = stat[user] + 1

            sorted_stat = sorted(stat, key=stat.get)
            sorted_stat.reverse()

            sorted_dict = []
            for item in sorted_stat:
                if stat[item] > 1:
                    sorted_dict.append(dict(
                        user = item,
                        count = stat[item],
                    ))


            statistic.statistics = simplejson.dumps(sorted_dict)
            statistic.put()
            rate_limit = twitter.getRateLimitStatus()['remaining_hits']

        else:
            from_db = True
            sorted_dict = simplejson.loads(statistic.statistics)

        user = User.get_by_key_name(twitter_id)

        template_values = {
            'user': user,
            'sorted_dict': sorted_dict,
            'total': total,
            'rate_limit': rate_limit,
            'last_check': statistic.updated + timedelta(hours=7),
            'from_db': from_db,
        }

        path = os.path.join(TEMPLATE, 'timeline.html')
        self.response.out.write(template.render(path, template_values))


#class TimelineApp(webapp.RequestHandler):
#
#    def get(self, username):
#        pass


application = webapp.WSGIApplication(
                [
                  ('/', HomeApp),
                  ('/connect', ConnectApp),
                  ('/callback', CallbackApp),
                  ('/timeline', TimelineApp),
                  #(r'/user/(.*)', UserApp),
                ],
                debug=DEBUG
              )

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
