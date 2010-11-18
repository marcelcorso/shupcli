from xml.dom import minidom

doc = minidom.parse('playground/entry.xml')
entry = doc.getElementsByTagName("entry")[0]
#print(entry.toxml())
data = {}

data['link'] = entry.getElementsByTagName('link')[0].getAttribute('href')
data['published'] = entry.getElementsByTagName('published')[0].firstChild.nodeValue
data['title'] = entry.getElementsByTagName('title')[0].firstChild.nodeValue
data['summary'] = entry.getElementsByTagName('summary')[0].firstChild.nodeValue

print(data)
