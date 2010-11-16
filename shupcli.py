import os
import cgi
import urllib
import logging
import feedparser
from django.utils import simplejson as json
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

#----------------
# Models

class Feed(db.Model):
  url = db.StringProperty(multiline=False)
  date = db.DateTimeProperty(auto_now_add=True)
  hub = db.StringProperty(multiline=False)

  def get_hub(self):
    # request and parse feed
    d = feedparser.parse(self.url)
    # get the hub
    # <link rel='hub' href='http://pubsubhubbub.appspot.com/'/>
    link = (link for link in d.feed.links if link['rel'] == 'hub' ).next()
    if link:
      self.hub = link['href']
      self.put()
    else:
      raise Exception('booo. this feed haz no hub link')  
  
  def sub(self):
    # Send an POST request to http://tumblr.superfeedr.com, with the following params :
    #   hub.mode : subscribe or unsubscribe
    #   hub.verify : sync or async
    #   hub.callback : http://domain.tld/your/callback
    #   hub.topic : http//feed.you.want.to/subscribe/to
    if self.hub:
      f = urllib.urlopen(self.hub, urllib.urlencode({
          'hub.mode' : 'subscribe',
          'hub.verify' : 'async',
          'hub.callback' : 'http://shupcli.appspot.com/pub',
          'hub.topic' : self.url
        })); 
      text = f.read()
      logging.info(text) 


class Post(db.Model):
  content = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)


#----------------
# RequestHandlers

class FeedListHandler(webapp.RequestHandler):
  # list feeds
  def get(self):
    feed_list = db.GqlQuery("SELECT * FROM Feed ORDER BY date DESC")
    template_values = {'feed_list': feed_list}
    path = os.path.join(os.path.dirname(__file__), 'feeds.html')
    self.response.out.write(template.render(path, template_values))

  # add a feed
  def post(self):
    feed = Feed()
    feed.url = self.request.get('url')
    feed.put()
    self.redirect('/feeds')

class FeedHandler(webapp.RequestHandler):
  def get(self, action, key):
    template_values = {}
    feed = db.get(key)
    logging.error(dir(feed))
    getattr(self, action)(feed)

  def show(self, feed):
    template_values = {'feed': feed, 
                       'posts': db.GqlQuery("SELECT * FROM Post WHERE url = :1 ORDER BY date DESC", feed.url)}
    path = os.path.join(os.path.dirname(__file__), 'feed.html')
    self.response.out.write(template.render(path, template_values))

  def get_hub(self, feed):
    feed.get_hub()
    self.redirect('/feeds/show/' + str(feed.key()))

  def sub(self, feed):
    feed.sub()
    self.redirect('/feeds/show/' + str(feed.key()))

  def unsub(self, feed):
    feed.unsub()
    self.redirect('/feeds/show/' + str(feed.key()))

 
class PubHandler(webapp.RequestHandler):

  def post(self):
    print 'Content-Type: text/plain'
    print ''
    print self.request.get('hub.challenge')
    logging.info(self.request.body)


application = webapp.WSGIApplication(
                                     [('/', FeedListHandler),
                                      ('/feeds', FeedListHandler),
                                      (r'/feeds/(\w+)/(\w+)', FeedHandler),
                                      ('/pub', PubHandler)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
