"""Adapter to run web.py applications using tornado web server.

http://www.tornadoweb.org/
"""
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpserver
import logging

import sys
import urllib
import web
from cStringIO import StringIO

class IOLoop(tornado.ioloop.IOLoop):
    def __init__(self, impl=None):
        self.current_fd = None
        self.tree = {}
        self._local = {}
        tornado.ioloop.IOLoop.__init__(self, impl)

    def add_handler(self, fd, handler, events):
        def xhandler(_fd, _events):
            self.current_fd = _fd
            return handler(_fd, _events)
            
        tree = self.tree.get(self.current_fd, [])
        if self.current_fd:
            tree = [self.current_fd] + tree
        self.tree[fd] = [fd] + tree
            
        tornado.ioloop.IOLoop.add_handler(self, fd, xhandler, events)

    def remove_handler(self, fd):
        tornado.ioloop.IOLoop.remove_handler(self, fd)
        del self.tree[fd]
        self._local.pop(fd, None)
        
    def get_tree(self):
        return self.tree[self.current_fd]
        
    def get_local(self):
        for fd in self.get_tree():
            if fd in self._local:
                return self._local[fd]
                
    def setup_local(self):
        self._local[self.current_fd] = web.storage()

def get_ioloop():
    return tornado.ioloop.IOLoop.instance()
    
def make_wsgi_environ(request):
    """Makes wsgi environment using Tornado HTTPRequest"""
    env = {}
    env['REQUEST_METHOD'] = request.method
    env['SCRIPT_NAME'] = ""
    env['PATH_INFO'] = urllib.unquote(request.path)
    env['QUERY_STRING'] = request.query
    
    special = ['CONTENT_LENGTH', 'CONTENT_TYPE']
    
    for k, v in request.headers.items():
        k =  k.upper().replace('_', '-')
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

def runtornado(func, port):
    """Run wsgi func using tornado http server."""
    tornado.ioloop.IOLoop._instance = IOLoop()
    web.utils.ThreadedDict._getd = get_ioloop().get_local

    class MainHandler(tornado.web.RequestHandler):
        def delegate(self):
            get_ioloop().setup_local()
            env = make_wsgi_environ(self.request)
            out = func(env, self._start_response)
            
            if not hasattr(out, 'next'):
                out = [out]
                
            for x in out:
                self.write(web.safestr(x))

        def _start_response(self, status, headers):
            status_code = int(status.split()[0])
            self.set_status(status_code)
            for name, value in headers:
                self.set_header(name, value)
            
        get = post = put = delete = delegate

    settings = {
        "static_path": "static"
    }
    application = tornado.web.Application([
        (r"/.*", MainHandler),
    ], **settings)
    if isinstance(port, tuple):
        _, port = port
    port = int(port)

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    print 'http://0.0.0.0:%d' % port
    tornado.ioloop.IOLoop.instance().start()
