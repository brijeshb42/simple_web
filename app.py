from webargs import fields

from simple_web.exceptions import NotFound, Unauthenticated
from simple_web.werkzeug import SimpleWeb  # or bottle or falcon
from simple_web.decorators import profile, login_required, validate
from simple_web.context import context


app = SimpleWeb()


@app.before_request
def before():
    print('Before request')


@app.after_request
def after(response):
    return response


@app.login_handler
def before_request():
    request = context.request
    token = request.headers.get('X-Auth-Token', '')
    if not token:
        token = request.cookies.get('token', '')
    if not token:
        raise Unauthenticated('Please login to access this resource.')


# @profile
@login_required
@validate({
    'name': fields.Integer(required=True, locations=('view_args',)),
    'num': fields.Integer(required=True, locations=('args',))
})
def get(**kwargs):
    request = context.request
    return {
        # 'va': args,
        'vk': kwargs,
        'args': request.args,
        'form': request.form
    }


def post(name=''):
    # raise NotFound('Post not found')
    request = context.request
    print(name)
    print(request.args)
    print(request.form)
    print(request.files)
    # print(request.json)
    return 'POST'


@login_required
def delete(*args, **kw):
    return 'DELETE'


def put():
    return 'PUT'


def patch(id):
    return 'PATCH {}'.format(id)


app.add_routes('/<int:name>', {
    'get': get,
    'post': get,
    'put': put,
    'patch': patch,
    'delete': delete
})

app.add_route('/', get)

if __name__ == '__main__':
    app.run('0.0.0.0', 8081, use_reloader=True, use_debugger=True)
