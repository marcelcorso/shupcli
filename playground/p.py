import urllib
import urllib2

hub_url = 'http://tumblr.superfeedr.com'
feed_url = 'http://marcelcorso.tumblr.com/rss'

data = urllib.urlencode({
  'hub.mode' : 'subscribe',
  'hub.verify' : 'async',
  'hub.callback' : 'http://shupcli.appspot.com/pub',
  'hub.topic' : feed_url
})
      
print('data: \n')
print(data)
req = urllib2.Request(hub_url, data)
req.timeout = 10
try:
  f = urllib2.urlopen(req)
  text = f.read()
  print("result: \n\n")
  print(text)
except urllib2.HTTPError as error:        
  if((error.code != 204) and (error.code != 202)): # No Content
    raise error
    # 204: we are subscribed. 202 the hub will see a bout it later







