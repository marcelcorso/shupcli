import feedparser

url = 'http://marcelmisunderstands.blogspot.com/feeds/posts/default?alt=rss'
d = feedparser.parse(url)
link = (link for link in d.feed.links if link['rel'] == 'hub' ).next()
