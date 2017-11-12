import inspect
import time
from functools import wraps

import simple_web.constants as constants
from simple_web.logger import logger


def set_attribute(name, value):
    def decorator(func):
        # @wraps(func)
        # def decorated_func(*args, **kwargs):
        #     return func(*args, **kwargs)
        setattr(func, name, value)
        # return decorated_func
    return decorator


def login_required(func):
    @wraps(func)
    def decorated_func(*args, **kwargs):
        signature = inspect.signature(func)
        if '__user_id' not in signature.parameters:
            kwargs.pop('__user_id')
        return func(*args, **kwargs)
    new_func = set_attribute(constants.LOGIN_REQUIRED, True)(decorated_func)
    return new_func


def csrf_required(func):
    return set_attribute(constants.CSRF_REQUIRED, func)


def validate(validator):
    return set_attribute(constants.VALIDATOR, validator)


def profile(f):
    """
    Decorate a function with this to know its running time.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        strt = time.time()
        logger.info('Calling function %s @ %f' % (f.__name__, strt))
        res = f(*args, **kwargs)
        end = time.time()
        logger.info('Finished function %s @ %f' % (f.__name__, end))
        logger.info('Time taken : %f ms' % (end - strt))
        return res
    return decorated_function
