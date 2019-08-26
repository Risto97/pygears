import inspect
from pygears.core.gear_decorator import create_gear_definition
from pygears.core.gear_decorator import FunctionMaker
from pygears.core.util import doublewrap, get_function_context_dict
from pygears.core.util import is_standard_func
from pygears.util.utils import gather


@doublewrap
def datagear(func, **meta_kwds):
    if not is_standard_func(func):
        raise Exception('Only regular functions can be converted to a @datagear.')

    paramspec = inspect.getfullargspec(func)

    invocation = ['*data']

    for name in paramspec.kwonlyargs:
        invocation.append(f'{name}={name}')

    body = f'''async with gather({",".join(paramspec.args)}) as data:
        yield datafunc({",".join(invocation)})'''

    execdict = {'datafunc': func, 'gather': gather}
    execdict.update(get_function_context_dict(func))

    gear_func = FunctionMaker.create(obj=func,
                                     body=body,
                                     evaldict=execdict,
                                     isasync=True,
                                     addsource=True)

    return create_gear_definition(gear_func, hdl={'compile': True})
