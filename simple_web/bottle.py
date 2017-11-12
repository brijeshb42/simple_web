from functools import wraps

import bottle
from bottle import LocalRequest

from simple_web.base import BaseApp, BaseRequest as SwRequest
from simple_web.context import context


class Request(SwRequest, LocalRequest):

    @property
    def args(self):
        return self.query.dict

    @property
    def form(self):
        return self.forms.dict


def _before_request_decorator(func):
    @wraps(func)
    def decorated_func(*args, **kwargs):
        context.request = bottle.request
        return func(*args, **kwargs)
    return decorated_func


class SimpleWeb(BaseApp):

    request_class = Request

    def __init__(self, request_class=Request):
        if request_class:
            self.request_class = request_class

        bottle.request = self.request_class()
        self.app = bottle.Bottle(autojson=True)

        self._before_request_hooks = []
        self._before_response_hooks = []

    def add_route(self, uri, handler, endpoint=None, methods=('GET',)):
        for method in methods:
            self.app.route(
                uri,
                method,
                _before_request_decorator(handler),
                endpoint
            )

    def add_routes(self, uri, handlers={}, endpoint=None):
        keys = handlers.keys()
        if not len(keys):
            return
        for key in keys:
            handler = handlers[key]
            self.add_route(
                uri, handler, endpoint=endpoint, methods=(key.upper(),))

    def before_request(self, handler):
        self._before_request_hooks.append(handler)
        return handler

    def after_request(self, handler):
        self._before_response_hooks.append(handler)
        return handler

    def wsgi_app(self, environ, start_response):
        return self.app.__call__(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def run(
            self, host='', port=5000,
            use_reloader=False,
            use_debugger=False,
            **kwargs):
        self.app.run(
            host=host, port=port,
            reloader=use_reloader,
            debug=use_debugger,
            **kwargs)
