# vim: set expandtab

from datetime import datetime, timedelta

from google.appengine.api import taskqueue 
from google.appengine.api import users
from google.appengine.api.taskqueue import Task, Queue
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

        self.redirect('/user')


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
        username = authorized_tokens['screen_name']

        statistic = UserStatistic.get_by_key_name(twitter_id)
        if statistic is None:
            statistic = UserStatistic(
                                      key_name=twitter_id,
                                      twitter_id=long(twitter_id),
                                     )
            statistic.put()

        if statistic.created == statistic.updated \
            or not statistic.statistics \
            or statistic.updated + timedelta(hours=1) < datetime.now():

            try:
                #taskqueue.add(url='/fetch', 
                #              name=twitter_id,
                #              params={'twitter_id': twitter_id}, 
                #              countdown=120)
                task = Task(url='/fetch',
                         name=twitter_id,
                         countdown=120,
                         params={'twitter_id': twitter_id})

                queue = Queue(name='fetch-tweets')
                queue.add(task)

            except:
                pass

        self.redirect('/user/%s' % username)

            #rate_limit = twitter.getRateLimitStatus()['remaining_hits']

        #else:
        #    from_db = True
        #    sorted_dict = simplejson.loads(statistic.statistics)
        #    total = statistic.total

        #user = User.get_by_key_name(twitter_id)

        #template_values = {
        #    'user': user,
        #    'sorted_dict': sorted_dict,
        #    'total': total,
        #    'rate_limit': rate_limit,
        #    'last_check': statistic.updated + timedelta(hours=7),
        #    'start_time': statistic.start_time + timedelta(hours=7),
        #    'end_time': statistic.end_time + timedelta(hours=7),
        #    'from_db': from_db,
        #}

        #path = os.path.join(TEMPLATE, 'timeline.html')
        #self.response.out.write(template.render(path, template_values))


class FetchApp(webapp.RequestHandler):
    def post(self):
        twitter_id = self.request.get('twitter_id', None)
        if twitter_id is None:
            return

        user = User.get_by_key_name(twitter_id)

        twitter = Twython(
            twitter_token = CONSUMER_KEY,
            twitter_secret = CONSUMER_SECRET,
            oauth_token = user.oauth_token,
            oauth_token_secret = user.oauth_token_secret,
        )

        statistic = UserStatistic.get_by_key_name(twitter_id)

        #if statistic is None:
        #    statistic = UserStatistic(
        #                              key_name=twitter_id,
        #                              twitter_id=long(twitter_id),
        #                             )
        #    statistic.put()

        stat = dict()
        total = 0
        page = 0
        start_time = None
        end_time = None
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

                if end_time is None:
                    end_time = datetime \
                                     .strptime(tweets[0]['created_at'],
                                         "%a %b %d %H:%M:%S +0000 %Y")


                last_tweet = tweets[len(tweets) - 1]
                start_time = datetime \
                               .strptime(last_tweet['created_at'],
                                     "%a %b %d %H:%M:%S +0000 %Y")

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


        statistic.start_time = start_time
        statistic.end_time = end_time 
        statistic.total = total
        statistic.statistics = simplejson.dumps(sorted_dict)
        statistic.put()


class UserApp(webapp.RequestHandler):

    def get(self, username = None):
        if username is None:
            self.redirect('/user')
            return

        user = User.gql("WHERE username = :1", username)
        if user.count() == 0:
            self.redirect('/')
            return
        else:
            user = user[0]

        session = get_current_session()
        authorized_tokens = session.get('authorized_tokens', None)
        is_user = user.key().name() == authorized_tokens['user_id'] \
                    if authorized_tokens else False

        statistic = UserStatistic.get_by_key_name(user.key().name())
        if statistic.statistics:
            sorted_dict = simplejson.loads(statistic.statistics)

            template_values = {
                'user': user,
                'is_user': is_user,
                'sorted_dict': sorted_dict,
                'total': statistic.total,
                'last_check': statistic.updated \
                                + timedelta(hours=7),
                'start_time': statistic.start_time \
                                + timedelta(hours=7),
                'end_time': statistic.end_time \
                                          + timedelta(hours=7),
            }
        else:
            template_values = {
                'user': user,
                'is_user': is_user,
            }

        path = os.path.join(TEMPLATE, 'timeline.html')
        self.response.out.write(template.render(path, template_values))


application = webapp.WSGIApplication(
                [
                  ('/', HomeApp),
                  ('/connect', ConnectApp),
                  ('/callback', CallbackApp),
                  ('/user', TimelineApp),
                  ('/fetch', FetchApp),
                  (r'/user/(.*)', UserApp),
                ],
                debug=DEBUG
              )

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
