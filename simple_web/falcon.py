from wsgiref.simple_server import make_server
try:
    import simplejson as json
except ImportError:
    import json

import falcon

from simple_web.base import BaseApp, BaseRequest
from simple_web.context import context
from simple_web.logger import logger


class Request(BaseRequest, falcon.Request):

    @property
    def args(self):
        return self.params

    @property
    def form(self):
        return {}


def _get_handler_method(handler):
    def _handler_method(instance, request, response, *args, **kwargs):
        context.request = request
        result = handler(*args, **kwargs)
        if isinstance(result, (dict, )):
            response.body = json.dumps(result)
        else:
            response.body = result
            response.content_type = 'text/plain'
    return _handler_method


def _create_dynamic_resource(methods, handler):
    method_map = {}

    for method in methods:
        method_name = 'on_{}'.format(method.lower())
        method_map[method_name] = _get_handler_method(handler)
    return type('DynamicResource', (object,), method_map)


def _dynamic_resource_from_method_map(handlers={}):
    keys = handlers.keys()
    if not len(keys):
        return None
    method_map = {}
    for key in keys:
        method_name = 'on_{}'.format(key.lower())
        method_map[method_name] = _get_handler_method(handlers[key])
    return type('DynamicResource', (object, ), method_map)


class SimpleWeb(BaseApp):

    request_class = Request

    def __init__(self, request_class=Request):
        if request_class:
            self.request_class = request_class
        self.app = falcon.API(request_type=self.request_class)

    def add_route(self, uri, handler, endpoint=None, methods=('GET',)):
        Resource = _create_dynamic_resource(methods, handler)
        self.app.add_route(uri, Resource())

    def add_routes(self, uri, handlers={}, endpoint=None):
        Resource = _dynamic_resource_from_method_map(handlers)
        if Resource:
            self.app.add_route(uri, Resource())

    def wsgi_app(self, environ, start_response):
        return self.app.__call__(environ, start_response)

    def run(self, host='', port=5000, **kwargs):
        server = make_server('', port, self)
        logger.info('Running development server on port {}'.format(port))
        server.serve_forever()
