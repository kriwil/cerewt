from google.appengine.ext import db


class User(db.Model):
    '''
    Model for User (twitter user it is).
    Use twitter_id as key_name in order to maintain uniqueness.
    '''

    twitter_id = db.IntegerProperty(required=True)
    username = db.StringProperty()
    oauth_token = db.StringProperty()
    oauth_token_secret = db.StringProperty()

    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)

    deleted = db.BooleanProperty(required=True, default=False)

