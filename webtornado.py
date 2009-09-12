"""Python module to run WSGI applications using tornado web server.

http://www.tornadoweb.org/
"""
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpserver
import logging

import sys
import urllib
from cStringIO import StringIO

class SocketThread:
    """In Tornado http server, the stream of execution are associated with sockets. 
    This class provides thread like interface for those streams of execution.
    """
    def __init__(self, fd, parent):
        self.fd = fd
        self.parent = parent
        self.local = None

    def get_local(self):
        if self.local is not None:
            return self.local
        else:
            return self.parent and self.parent.get_local()

    @staticmethod
    def get_current_thread():
        return tornado.ioloop.IOLoop().instance().active_thread

class IOLoop(tornado.ioloop.IOLoop):
    """IOLoop extension to support SocketThreads."""
    def __init__(self, impl=None):
        self.threads = {}
        self.active_thread = None
        tornado.ioloop.IOLoop.__init__(self, impl)

    def add_handler(self, fd, handler, events):
        def xhandler(_fd, _events):
            self.active_thread = self.threads[_fd]
            return handler(_fd, _events)
            
        self.threads[fd] = SocketThread(fd, self.active_thread)
        tornado.ioloop.IOLoop.add_handler(self, fd, xhandler, events)

    def remove_handler(self, fd):
        tornado.ioloop.IOLoop.remove_handler(self, fd)
        del self.threads[fd]

tornado.ioloop.IOLoop._instance = IOLoop()
                
class WSGIHandler(tornado.web.RequestHandler):
    """WSGI Handler for Tornado."""
    def __init__(self, application, request, wsgi_app):
        self.wsgi_app = wsgi_app
        tornado.web.RequestHandler.__init__(self, application, request)

    def delegate(self):
        env = self.make_wsgi_environ(self.request)
        out = self.wsgi_app(env, self._start_response)
        
        if not (hasattr(out, 'next') or isinstance(out, list)):
            out = [out]
        
        # don't send any data for redirects
        if self._status_code not in [301, 302, 303, 304, 307]:
            for x in out:
                self.write(x)

    get = post = put = delete = delegate

    def _start_response(self, status, headers):
        status_code = int(status.split()[0])
        self.set_status(status_code)
        for name, value in headers:
            self.set_header(name, value)

    def make_wsgi_environ(self, request):
        """Makes wsgi environment using Tornado HTTPRequest"""
        env = {}
        env['REQUEST_METHOD'] = request.method
        env['SCRIPT_NAME'] = ""
        env['PATH_INFO'] = urllib.unquote(request.path)
        env['QUERY_STRING'] = request.query
        
        special = ['CONTENT_LENGTH', 'CONTENT_TYPE']
        
        for k, v in request.headers.items():
            k =  k.upper().replace('-', '_')
            if k not in special:
                k = 'HTTP_' + k
            env[k] = v
            
        env["wsgi.url_scheme"] = request.protocol
        env['REMOTE_ADDR'] = request.remote_ip
        env['HTTP_HOST'] = request.host
        env['SERVER_PROTOCOL'] = request.version
        
        if request.body:
            env['wsgi.input'] = StringIO(request.body)
            
        env['wsgi.errors'] = sys.stdout    
        env['wsgi.multithread'] = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once'] = False
            
        return env

class WSGIServer(tornado.httpserver.HTTPServer):
    """Tornado HTTP Server to work with wsgi applications."""
    def __init__(self, wsgi_app):
        application = tornado.web.Application([
            (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"}),
            (r"/.*", WSGIHandler, {'wsgi_app': wsgi_app}),
        ])
        tornado.httpserver.HTTPServer.__init__(self, application)

class SocketLocalMiddle:
    """WSGI middleware to setup socket-local for request handling socket-thread."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, env, start_response):
        SocketThread.get_current_thread().local = {}
        return self.wsgi_app(env, start_response)

def start(wsgi_app, port):
    """Starts Tornado HTTP Server on specified port with the specified wsgi_app."""
    # setup socket-local for request hanling socket-thread
    wsgi_app = SocketLocalMiddle(wsgi_app)

    # enable pretty logging
    logging.getLogger().setLevel(logging.INFO)
    tornado.options.enable_pretty_logging()
    
    # start the server
    http_server = WSGIServer(wsgi_app)
    http_server.listen(port)
    print 'http://0.0.0.0:%d' % port
    tornado.ioloop.IOLoop.instance().start()

def start_webpy(wsgi_app, port):
    """This should go into web.py"""
    if isinstance(port, tuple):
        _, port = port
    port = int(port)

    import web

    # monkey-patch web.ThreadedDict
    class ThreadedDict(web.ThreadedDict):
        def getd(self):
            local = SocketThread.get_current_thread().get_local()
            if self not in local:
                local[self] = web.storage()
            return local[self]

    web.ThreadedDict = web.threadeddict = web.utils.ThreadedDict = web.utils.threadeddict = ThreadedDict
    start(wsgi_app, port)

runtornado = start_webpy
