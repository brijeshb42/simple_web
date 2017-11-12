from simple_web.exceptions import NotFound
from simple_web.werkzeug import SimpleWeb  # or bottle or falcon
from simple_web.decorators import profile
from simple_web.context import context


app = SimpleWeb()


@app.before_request
def before():
    print('Before request')


@app.after_request
def after(response):
    return response


@app.get('/')
@profile
def get(*args, **kwargs):
    request = context.request
    return {
        'va': args,
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


def delete():
    return 'DELETE'


def put():
    return 'PUT'


def patch(id):
    return 'PATCH {}'.format(id)


app.add_routes('/<name>', {
    'GET': get,
    'POST': post,
    'PUT': put,
    'PATCH': patch,
    'DELETE': delete
})

app.add_route('/', get)

if __name__ == '__main__':
    app.run('0.0.0.0', 8081, use_reloader=True, use_debugger=True)
