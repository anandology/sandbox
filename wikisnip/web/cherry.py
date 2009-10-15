import wsgiserver
    
def forum(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type','text/plain')]
    start_response(status, response_headers)
    return ['Hello world from a forum!\n']
    
def blog(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type','text/plain')]
    start_response(status, response_headers)
    return [b'Hello world from a blog!\n']
    
# Here we set our application to the script_name '/' 
wsgi_apps = [('/blog', blog), ('/forum', forum)]
    
server = wsgiserver.CherryPyWSGIServer(('localhost', 8080), wsgi_apps, server_name='localhost')

if __name__ == '__main__':
   try:
      server.start()
   except KeyboardInterrupt:
      server.stop()

