try:
    import simplejson as json
except ImportError:
    import json
from functools import wraps

from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request as RequestBase, Response
from werkzeug.exceptions import HTTPException
from werkzeug.contrib.wrappers import JSONRequestMixin
from werkzeug.serving import run_simple

from simple_web.base import BaseApp, BaseRequest as SwRequest
from simple_web.exceptions import SimpleWebException as SWException
from simple_web.context import context
from simple_web.logger import logger
import simple_web.constants as constants


MIMETYPE_JSON = 'application/json'


def dispatch_options_handler(adapter):
    response = Response(status=204)
    response.headers.set('Allow', ', '.join(adapter.allowed_methods()))
    return response


class Request(SwRequest, RequestBase, JSONRequestMixin):
    pass


class SimpleWeb(BaseApp):

    request_class = Request

    def __init__(self, request_class=Request):
        if request_class:
            self.request_class = request_class
        self.url_map = Map()
        self.handler_map = {}

        self._before_request_hooks = []
        self._before_response_hooks = []
        self._login_hooks = []

    def add_route(
            self, uri, handler,
            endpoint=None, methods=('GET',),
            login_required=False):
        if not endpoint:
            endpoint = uri + '-' + handler.__name__
        self.url_map.add(Rule(uri, endpoint=endpoint, methods=methods))
        _protect = getattr(handler, constants.LOGIN_REQUIRED, login_required)
        if _protect:
            handler = self._protect_resource(handler)
        self.handler_map[endpoint] = handler

    def add_routes(
            self, uri, handlers={}, endpoint=None, login_required=False):
        keys = handlers.keys()
        if not len(keys):
            return
        for key in keys:
            handler = handlers[key]
            self.add_route(
                uri, handler, endpoint=endpoint,
                methods=(key.upper(),),
                login_required=login_required
            )

    def before_request(self, handler):
        self._before_request_hooks.append(handler)
        return handler

    def after_request(self, handler):
        self._before_response_hooks.append(handler)
        return handler

    def login_handler(self, handler):
        self._login_hooks.append(handler)
        return handler

    def wsgi_app(self, environ, start_response):
        request = self.request_class(environ)
        response = self._dispatch_request(request)
        return response(environ, start_response)

    def run(self, host='', port=5000, **kwargs):
        logger.info('Running development server on port {}'.format(port))
        run_simple('0.0.0.0', 8081, self, **kwargs)

    def _protect_resource(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for hook in self._login_hooks:
                hook()
            return func(*args, **kwargs)
        return wrapper

    def _dispatch_before_req_hooks(self):
        for hook in self._before_request_hooks:
            hook()

    def _dispatch_before_resp_hooks(self, response):
        for hook in self._before_response_hooks:
            resp = hook(response)
            if resp:
                response = resp
        return response

    def _dispatch(self, adapter):
        status_code = 200
        mimetype = 'text/plain'
        try:
            endpoint, values = adapter.match()
        except HTTPException as e:
            status_code = e.code
            result = SWException(
                code=status_code,
                description=e.description
            ).to_dict()
        else:
            try:
                handler = self.handler_map[endpoint]
                result = handler(**values)
                if isinstance(result, Response):
                    return result
            except SWException as e:
                result = e.to_dict()
                status_code = e.code
            except Exception as e:
                logger.exception('Error while handling {}'.format(endpoint), e)
                result = 'Server error'
                status_code = 500
        if isinstance(result, (dict,)):
            result = json.dumps(result)
            mimetype = MIMETYPE_JSON
        return Response(result, status=status_code, mimetype=mimetype)

    def _dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request)
        if request.method == 'OPTIONS':
            return dispatch_options_handler(adapter)
        context.request = request
        self._dispatch_before_req_hooks()
        response = self._dispatch(adapter)
        return self._dispatch_before_resp_hooks(response)
