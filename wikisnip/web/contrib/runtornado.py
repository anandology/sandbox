"""Adapter to run web.py applications using tornado web server.

http://www.tornadoweb.org/
"""
import web

def runtornado(func, port):
    import tornado.ioloop
    import tornado.options
    import tornado.web
    import logging

    class MainHandler(tornado.web.RequestHandler):
        def delegate(self):
            
            pass

        get = post = put = delete = delegate

