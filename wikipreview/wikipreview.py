import itertools
import urllib2
import urlparse
from BeautifulSoup import BeautifulSoup
import web

try:
    from google.appengine.api import urlfetch
except ImportError:
    urlfetch = None

def wget(url):
    if urlfetch:
        return urlfetch.fetch(url).content
    else:
        req = urllib2.Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Compatible)")
        return urllib2.urlopen(req).read()

def wiki_preview(url):
    html = wget(url)
    soup = BeautifulSoup(html)

    div = soup.find('div', {'id': 'bodyContent'})
    x = BeautifulSoup('<div class="wikipedia-preview">')

    for node in div.childGenerator():
        if (isinstance(node, basestring) or
            node.name.lower() in ["table", "script"] or
            node.get('id') in ["siteSub", "contentSub", "jump-to-nav"] or
            node.get('class') in ['dablink', 'toclimit-2']):
            continue

        if node.name.lower() == "h2":
            break
        x.append(node)

    for a in x.findAll('a'):
        if a.get('href'):
            a['href'] = urlparse.urljoin(url, a['href'])

    return x

urls = (
    "/", "Index",
    "/w/.*", "notfound",
    "/favicon.ico", "notfound",
    "/en/(.*).txt", "PreviewText",
    "/en/(.*)", "Preview",
)

class notfound:
    def GET(self):
        raise web.notfound("")

class Index:
    def GET(self):
        return "Wikipedia Preview"

class Preview:
    def GET(self, name):
        url = "http://en.wikipedia.org/wiki/" + name
        preview = wiki_preview(url).prettify()

        web.header('Content-Type', 'text/html; charset=utf-8')
        yield '<htm>'
        yield '<head><title>%s</title><link rel="stylesheet" type="text/css" href="/static/style.css"/></head>' % name
        yield '<body>'
        yield preview
        yield '</body></html>'

class PreviewText:
    def GET(self, name):
        web.header('Content-Type', 'text/plain; charset=utf-8')

        url = "http://en.wikipedia.org/wiki/" + name
        preview = wiki_preview(url)
        return u''.join(preview.findAll(text=True)) 

app = web.application(urls, globals())
main = app.cgirun()
