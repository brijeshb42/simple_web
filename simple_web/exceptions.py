class SimpleWebException(Exception):
    code = 400
    description = 'Some error occurred'

    def __init__(
            self,
            description=None,
            code=None,
            **kw):
        self.description = description or self.__class__.description
        self.code = code or self.__class__.code
        self.data = kw

    def to_dict(self):
        result = {
            'code': self.code,
            'description': self.description
        }
        if self.data:
            result['data'] = self.data
        return dict(**result)


class Unauthenticated(SimpleWebException):
    code = 401
    description = 'You are not logged in.'


class Unauthorized(SimpleWebException):
    code = 403
    description = 'You are not allowed to perform the operation.'


class NotFound(SimpleWebException):
    code = 404
    description = 'What you were looking for is not available.'


class InvalidData(SimpleWebException):
    code = 422
    description = 'You provided invalid data.'

    def __init__(self, error):
        self.error = error

    def to_dict(self):
        return dict(
            code=self.code,
            description=self.description,
            data=self.error.normalized_messages()
        )
