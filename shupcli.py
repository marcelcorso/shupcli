import os
import cgi
import urllib
import urllib2
import logging
import feedparser
from xml.dom import minidom
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
      logging.info('going to sub')
      logging.info('hub is @: ' + self.hub)
      data = urllib.urlencode({
          'hub.mode' : 'subscribe',
          'hub.verify' : 'async',
          'hub.callback' : 'http://shupcli.appspot.com/pub',
          'hub.topic' : self.url
        })
      logging.info('data: ' + data)
      req = urllib2.Request(self.hub, data)
      req.timeout = 10 # GAE is picky about this and will throw "DownloadError 5" (timeout) for everything
      try:
        f = urllib2.urlopen(req)
        text = f.read()
        logging.info('info: ' + str(f.info()))
        logging.info('response: ' + text)
      except urllib2.HTTPError, error:
        # print('lala')
        # print(error.code) 
        if (error.code != 204) and (error.code != 202): # No Content
          raise
        else:
          # 204 means that we are subscribed. 202 means its going to be done later
          logging.info('sub response status: ' + str(error.code))

class Post(db.Model):
  request_body = db.TextProperty()
  request_headers = db.StringProperty(multiline=True)
  date = db.DateTimeProperty(auto_now_add=True)
  
  published = db.StringProperty(multiline=False)
  title = db.StringProperty(multiline=False)
  summary =  db.TextProperty()
  link =  db.StringProperty(multiline=False)  

  def parse(self):
    logging.info('parsing...')
    doc = minidom.parseString(self.request_body)
    entry = doc.getElementsByTagName("entry")[0]
    self.link = entry.getElementsByTagName('link')[0].getAttribute('href')
    self.published = entry.getElementsByTagName('published')[0].firstChild.nodeValue
    self.title = entry.getElementsByTagName('title')[0].firstChild.nodeValue
    if(entry.getElementsByTagName('summary')):
      self.summary = db.Text(entry.getElementsByTagName('summary')[0].firstChild.nodeValue)
    elif (entry.getElementsByTagName('content')):
      self.summary = db.Text(entry.getElementsByTagName('content')[0].firstChild.nodeValue)

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
    logging.info('PubHandler#post')
    logging.info(self.request.body)
    logging.info(self.request.headers)
    post = Post()
    post.request_body = db.Text(self.request.body)
    post.request_headers = str(self.request.headers)
    post.parse()
    post.put()

  # this is where we answer the confirmation callback
  def get(self):
    # hub.mode
    #   REQUIRED. The literal string "subscribe" or "unsubscribe", which matches the original request to the hub from the subscriber.
    # hub.topic
    #   REQUIRED. The topic URL given in the corresponding subscription request.
    # hub.challenge
    #   REQUIRED. A hub-generated, random string that MUST be echoed by the subscriber to verify the subscription.
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write(self.request.get('hub.challenge'))


logging.getLogger().setLevel(logging.DEBUG)
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
