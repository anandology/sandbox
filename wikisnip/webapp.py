import web
import wikisnip

urls = (
    "/w/.*", "notfound",
    "/favicon.ico", "notfound",
    "/en/(.*).txt", "PreviewText",
    "/en/(.*)", "Preview",
)
app = web.application(urls, globals())

class notfound:
    def GET(self):
        raise web.notfound("")

class Preview:
    def GET(self, name):
        url = "http://en.wikipedia.org/wiki/" + name
        preview = wikisnip.wikisnip(url).prettify()

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

main = app.cgirun()
