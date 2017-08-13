import datetime
import inspect
import logging
import time

from functools import wraps

def traceme(logf):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

            try:
                filename = inspect.getsourcefile(func)
                lineno   = inspect.getsourcelines(func)[1]
            except TypeError:
                filename = ''
                lineno   = 0

            funcname = func.__name__

            params = []

            for arg in args:
                if isinstance(arg, (str, unicode)):
                    param = '"{0}"'.format(arg)
                else:
                    param = str(arg)

                params.append(param)

            for key, value in kwargs:
                if isinstance(value, (str, unicode)):
                    v = '"{0}"'.format(value)
                else:
                    v = str(value)

                param = '{0}={1}'.format(key, v)
                params.append(param)

            arg_expr = ', '.join(params)

            t1 = time.time()
            ret = func(*args, **kwargs)
            t2 = time.time()

            duration = t2 - t1

            log = '[{timestamp}] {filename}<{lineno}> {funcname}({args}) => ({duration} sec)\n'.format(
                timestamp=timestamp,
                filename=filename,
                lineno=lineno,
                funcname=funcname,
                args=arg_expr,
                duration=duration
            )

            logf(log)

            return ret

        return wrapper

    return decorator

@traceme(logging.debug)
def f(x):
    print('I received: {0}'.format(x))

def main():
    logging.basicConfig(level=logging.DEBUG)
    f(3)

if __name__ == '__main__':
    main()
