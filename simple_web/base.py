from functools import wraps


class BaseApp(object):

    def add_route(self, uri, handler, endpoint=None, methods=('GET',)):
        raise NotImplementedError()

    def add_routes(self, uri, handlers={}, endpoint=None):
        raise NotImplementedError()

    def before_request(self, handler):
        raise NotImplementedError()

    def after_request(self, handler):
        raise NotImplementedError()

    def route(self, uri, methods=('GET',), endpoint=None):

        def decorator(func):
            self.add_route(uri, func, methods=methods, endpoint=endpoint)
            return func

        return decorator

    def get(self, uri, handler=None):
        if not handler:
            return self.route(uri)
        self.add_route(uri, handler)

    def post(self, uri):
        return self.route(uri, methods=('POST',))

    def put(self, uri):
        return self.route(uri, methods=('PUT',))

    def patch(self, uri):
        return self.route(uri, methods=('PATCH',))

    def delete(self, uri):
        return self.route(uri, methods=('DELETE',))

    def wsgi_app(self, environ, start_response):
        raise NotImplementedError()

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def run(self, host='', port=5000, **kwargs):
        raise NotImplementedError()


class BaseRequest(object):
    pass
