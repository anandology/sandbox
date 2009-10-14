"""Library to convert wikipedia articles to plain text.
"""

__author__ = "Anand Chitipothu <anandology@gmail.com>"
__all__ = ["get_wikitext", "make_webapp"]

import simplejson
import urllib
import re

try:
    import web
except:
    web = None

def get_wikitext(name):
    """Returns wikipedia article with the given name in plaintext.
    """
    # Query wikipedia to get JSON representation of the page.
    url = "http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles=" + name
    json = urllib.urlopen(url).read()
    data = simplejson.loads(json)
    text = data['query']['pages'].values()[0]['revisions'][0]['*']

    # remove markup
    text = re_compile(r'<!--[^<>]*-->').sub('', text)
    text = re_compile(r'\[\[([^\[]*)\]\]').sub(lambda m: m.group(1).split('|')[-1], text)
    return text

regex_cache = {}
def re_compile(pattern):
    """utility memoize regular expressions"""
    if pattern not in regex_cache:
        regex_cache[pattern] = re.compile(pattern)
    return regex_cache[pattern]

def parse_txt(self, text):
    text = re_compile(r'<!--[^<>]*-->').sub('', text)
    text = re_compile(r'\[\[([^\[]*)\]\]').sub(lambda m: m.group(1).split('|')[-1], text)
    rx = re_compile('(<!--|-->|{\||\|})')
    tokens = rx.split(text)
    return text

class wikitext:
    def GET(self, name):
        web.header('content-type', 'text/plain')
        return get_wikitext(name)

def make_webapp():
    """Create a web.py application to server wikipedia in plaintext"""
    urls = (
        "/", "redirect Main_Page",
        "/(.*)", wikitext
    )
    return web.application(urls, {})

if __name__ == "__main__":
    make_webapp().run()
