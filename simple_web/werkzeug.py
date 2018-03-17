try:
    import simplejson as json
except ImportError:
    import json
from functools import wraps

from werkzeug.utils import cached_property
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request as RequestBase, Response
from werkzeug.exceptions import HTTPException
from werkzeug.contrib.wrappers import JSONRequestMixin
from werkzeug.serving import run_simple

from webargs import core, ValidationError

from simple_web.base import BaseApp, BaseRequest as SwRequest
from simple_web.exceptions import (
    SimpleWebException as SWException,
    InvalidData
)
from simple_web.context import context
from simple_web.logger import logger
import simple_web.constants as constants


MIMETYPE_JSON = 'application/json'


def dispatch_options_handler(adapter):
    response = Response(status=204)
    response.headers.set('Allow', ', '.join(adapter.allowed_methods()))
    return response


def validation_handler(error):
    """
    To be passed to flaskParser to throw custom error
    """
    raise InvalidData(error)


class Request(SwRequest, RequestBase, JSONRequestMixin):

    @cached_property
    def json(self):
        if self.headers.get('content-type') == 'application/json':
            return json.loads(self.data)


class WerkzeugParser(core.Parser):

    __location_map__ = dict(
        view_args='parse_view_args',
        **core.Parser.__location_map__
    )

    def __init__(self, view_args={}, **kw):
        super().__init__(**kw)
        self.view_args = view_args

    def parse_view_args(self, req, name, field):
        """Pull a value from the request's ``view_args``."""
        print(name, field)
        return core.get_value(self.view_args, name, field)

    def parse_json(self, req, name, field):
        json_data = req.json
        if json_data is None:
            return core.missing
        return core.get_value(json_data, name, field, allow_many_nested=True)

    def parse_querystring(self, req, name, field):
        """Pull a querystring value from the request."""
        return core.get_value(req.args, name, field)

    def parse_headers(self, req, name, field):
        """Pull a value from the header data."""
        return core.get_value(req.headers, name, field)

    def parse_cookies(self, req, name, field):
        """Pull a value from the cookiejar."""
        return core.get_value(req.cookies, name, field)

    def parse_files(self, req, name, field):
        """Pull a file from the request."""
        return core.get_value(req.files, name, field)

    def handle_error(self, error):
        """Handles errors during parsing. Aborts the current HTTP request and
        responds with a 422 error.
        """
        return error


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
        _validate = getattr(handler, constants.VALIDATOR, False)
        if _validate:
            handler = self._validate_resource(handler)
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

    def run(self, host='0.0.0.0', port=5000, **kwargs):
        logger.info('Running development server on port {}'.format(port))
        run_simple(host, port, self, **kwargs)

    def _protect_resource(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for hook in self._login_hooks:
                hook()
            return func(*args, **kwargs)
        return wrapper

    def _validate_resource(self, func):
        @wraps(func)
        def wrapper(**kwargs):
            validator = getattr(func, constants.VALIDATOR)
            parser = WerkzeugParser(kwargs, error_handler=validation_handler)
            try:
                data = parser.parse(validator, context.request)
            except ValidationError as e:
                raise InvalidData(error)
            else:
                return func(**data)
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
            response = dispatch_options_handler(adapter)
        else:
            context.request = request
            self._dispatch_before_req_hooks()
            response = self._dispatch(adapter)
        return self._dispatch_before_resp_hooks(response)
