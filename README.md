## Simple Web [WIP]

A functional way to develop web applications without worrying about framework specific tidbits.

> This is not yet another framework. It is an abstraction over existing frameworks (currently werkzeug, bottle and falcon supported) so that one can focus on actual arguments to the functions instead of extracting them from the framework's request and response objects.


### Usage

```python
from simple_web.werkzeug import SimpleWeb

# above, werkzeug can be changed to bottle or falcon

app = SimpleWeb()

def index():
    return "Hello World"

app.get('/', index)

app.run()
```


### TODO

[ ] Pass url params, query string and form data directly to functions
[ ] Add way to validate incoming data
[ ] Add support for login/auth
