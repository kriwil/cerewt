#!/bin/env python

from google.appengine.dist import use_library
use_library('django', '1.2')

import cgi
import csv
import hashlib
import logging
import math
import os
import pickle
import re

# from django.utils import simplejson as json

# from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
from google.appengine.ext.webapp.util import run_wsgi_app

from models import *
from settings import *

class HomeApp(webapp.RequestHandler):
	def get(self):

		limit = 10
		page = self.request.get('page') or 1
		page = int(page)
		offset = (page - 0) * limit

		place = Place.all()
		total_place = place.count()
		places = place.fetch(limit=limit, offset=offset)
		#max_row = int(float(len(places)) / 2)

		total_page = int(math.ceil(float(total_place) / limit))

		template_values = {
			'places': places,
			'total_place': total_place,
			'current_page': page,
			'prev_page': page - 1,
			'next_page': page + 1,
			'total_page': total_page,
			'loop_range': range(1, total_page),
			'current_url': '/?'
		}

		path = os.path.join(TEMPLATE, 'base.html')
		self.response.out.write(template.render(path, template_values))

class PlaceDetailApp(webapp.RequestHandler):
	def get(self, *args):
		place = Place.get_by_id(int(args[0]))
		if not args[1] or args[1] != place.url_name:
			self.redirect("/place/%s/%s" % (place.key().id(), place.url_name))

		template_values = {
			'place': place,
		}

		path = os.path.join(TEMPLATE, 'place_detail.html')
		self.response.out.write(template.render(path, template_values))

class SearchApp(webapp.RequestHandler):
	def get(self):
		keyword = self.request.get('keyword')

		limit = 10
		page = self.request.get('page') or 1
		page = int(page)
		offset = (page - 1) * limit

		indexes = db.GqlQuery("SELECT __key__ FROM PlaceIndex WHERE keyword = :keyword LIMIT %s, %s" % (offset, limit), keyword=keyword)
		keys = [k.parent() for k in indexes]
		places = db.get(keys)

		total_result = indexes.count()
		total_page = int(math.ceil(float(total_result) / limit))

		template_values = {
			'places': places,
			'total_place': total_result,
			'current_page': page,
			'prev_page': page - 1,
			'next_page': page + 1,
			'total_page': total_page,
			'loop_range': range(1, total_page),
			'keyword': keyword,
			'current_url': '/search?keyword=%s&' % keyword
		}

		path = os.path.join(TEMPLATE, 'search.html')
		self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication(
	            [
	              ('/', HomeApp),
	              (r'/place/([0-9]+)/([A-Za-z0-9-]*)', PlaceDetailApp),
	              ('/search', SearchApp),
	            ],
	            debug=DEBUG
	          )

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
