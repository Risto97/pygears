import copy
import inspect
import sys
import traceback
import inspect
from functools import wraps
import functools

from pygears.registry import PluginBase, bind, registry
from pygears.typing import Any

from .hier_node import NamedHierNode
from .infer_ftypes import TypeMatchError, infer_ftypes, type_is_specified
from .intf import Intf
from .partial import Definition
from .port import InPort, OutPort
from .util import doublewrap
from .type_match import type_match, TypeMatchError


class TooManyArguments(Exception):
    pass


class GearTypeNotSpecified(Exception):
    pass


class GearArgsNotSpecified(Exception):
    pass


def check_arg_num(argnames, varargsname, args):
    if (len(args) < len(argnames)) or (
            not varargsname and (len(args) > len(argnames))):
        balance = "few" if (len(args) < len(
            argnames)) else "many"

        raise TooManyArguments(
            f"Too {balance} arguments for the module {self.name} provided."
        )


def check_arg_specified(args):
    args_res = []
    for i, a in enumerate(args):
        if not isinstance(a, Intf):
            from pygears.common import const
            a = const(val=a)

        args_res.append(a)

        if not type_is_specified(a.dtype):
            raise GearArgsNotSpecified(
                f"Input arg {i} has unresolved type {repr(a.dtype)}")

    return tuple(args_res)


class GearBase(NamedHierNode):
    def __new__(cls, func, meta_kwds, *args, name=None, **kwds):

        if name is None:
            name = func.__name__

        kwds_comb = meta_kwds.copy()
        kwds_comb.update(kwds)

        gear = super().__new__(cls)
        gear.__init__(func, *args, name=name, **kwds_comb)
        enablement = gear.params.pop('enablement')
        print(enablement)

        if not enablement:
            gear.remove()
            raise TypeMatchError(
                f'Enablement condition failed: {meta_kwds["enablement"]}'
            )

        return gear.resolve()

    def __init__(self, func, *args, name=None, intfs=[], outnames=[], **kwds):
        super().__init__(name, registry('CurrentHier'))
        self.func = func
        self.__doc__ = func.__doc__

        self.outnames = outnames.copy()
        self.intfs = intfs.copy()
        self.in_ports = []
        self.out_ports = []

        self.args = args
        self.resolved = False

        argspec = inspect.getfullargspec(func)
        self.argnames = argspec.args
        self.varargsname = argspec.varargs
        self.annotations = argspec.annotations
        self.kwdnames = argspec.kwonlyargs

        check_arg_num(self.argnames, self.varargsname, self.args)
        try:
            self.args = check_arg_specified(self.args)
        except GearArgsNotSpecified as e:
            raise GearArgsNotSpecified(f'{str(e)}, when instantiating {self.name}')

        self.params = {}
        if isinstance(argspec.kwonlydefaults, dict):
            self.params.update(argspec.kwonlydefaults)

        self.params.update(kwds)

        self.params.update({
            a: (self.annotations[a] if a in self.annotations else Any)
            for a in self.argnames
        })

        self._handle_return_annot()
        self._expand_varargs()
        self.in_ports = [
            InPort(self, i, name) for i, name in enumerate(self.argnames)
        ]

        for i, a in enumerate(self.args):
            try:
                a.connect(self.in_ports[i])
            except AttributeError:
                raise GearArgsNotSpecified(
                    f"Input arg {i} for module {self.name} was not"
                    f" resolved to interface, instead {repr(a)} received")

        self.infer_params()

    def _handle_return_annot(self):
        if "return" in self.annotations:
            ret_anot = self.annotations["return"]
            if isinstance(ret_anot, dict):
                self.outnames = tuple(ret_anot.keys())
                self.params['return'] = tuple(ret_anot.values())
            else:
                self.params['return'] = ret_anot

    def _expand_varargs(self):
        if self.varargsname:
            vararg_type_list = []
            if self.varargsname in self.annotations:
                vararg_type = self.annotations[self.varargsname]
            else:
                vararg_type = Any
            # Append the types of the self.varargsname
            for i, a in enumerate(self.args[len(self.argnames):]):
                if isinstance(vararg_type, str):
                    # If vararg_type is a template string, it can be made
                    # dependent on the arguments position
                    type_tmpl_i = vararg_type.format(i).encode()
                else:
                    # Vararg is not a template and should be passed as is
                    type_tmpl_i = vararg_type

                argname = f'{self.varargsname}{i}'

                vararg_type_list.append(argname)
                self.params[argname] = type_tmpl_i
                self.argnames.append(argname)

            self.params[
                self.varargsname] = f'({", ".join(vararg_type_list)})'.encode(
                )

    def remove(self):
        for p in self.in_ports:
            if p.producer is not None:
                try:
                    p.producer.disconnect(p)
                except ValueError:
                    pass

        for p in self.out_ports:
            if p.producer is not None:
                p.producer.disconnect(p)

        super().remove()

    @property
    def definition(self):
        return self.params['definition']

    def set_ftype(self, ft, i):
        self.dtype_templates[i] = ft

    def is_specified(self):
        for i in self.intfs:
            if not type_is_specified(i.dtype):
                return False
        else:
            return True

    def get_arg_types(self):
        return tuple(a.dtype for a in self.args)

    def get_type(self):
        if len(self.intfs) > 1:
            return tuple(i.dtype for i in self.intfs)
        elif len(self.intfs) == 1:
            return self.intfs[0].dtype
        else:
            return None

    def infer_params(self):
        arg_types = {name: arg.dtype for name, arg in zip(self.argnames, self.args)}

        try:
            self.params = infer_ftypes(
                self.params,
                arg_types,
                namespace=self.func.__globals__,
                allow_incomplete=False)
        except TypeMatchError as e:
            raise TypeMatchError(f'{str(e)}, of the module {self.name}')

    def resolve(self):
        func_ret = self.resolve_func()

        if func_ret:
            out_dtype = tuple(r.dtype for r in func_ret)
        elif not isinstance(self.params['return'], tuple):
            out_dtype = (self.params['return'], )
        else:
            out_dtype = self.params['return']

        if (len(self.outnames) == 0) and (len(out_dtype) == 1):
            self.outnames.append('dout')
        else:
            for i in range(len(self.outnames), len(out_dtype)):
                self.outnames.append(f'dout{i}')

        self.out_ports = [
            OutPort(self, i, name) for i, name in enumerate(self.outnames)
        ]

        for i, r in enumerate(func_ret):
            r.connect(self.out_ports[i])

        if not self.intfs:
            self.intfs = [Intf(dt) for dt in out_dtype]

        assert len(self.intfs) == len(out_dtype)
        for intf, port in zip(self.intfs, self.out_ports):
            intf.source(port)

        if not self.is_specified():
            raise GearTypeNotSpecified(
                f"Output type of the module {self.name}"
                f" could not be resolved, and resulted in {repr(out_dtype)}")

        if len(self.intfs) > 1:
            return tuple(self.intfs)
        elif len(self.intfs) == 1:
            return self.intfs[0]
        else:
            return None


class Gear(GearBase):
    def resolve_func(self):
        return tuple()


class Hier(GearBase):
    def resolve_func(self):
        func_args = [Intf(a.dtype) for a in self.args]
        for arg, port in zip(func_args, self.in_ports):
            arg.source(port)

        func_kwds = {
            k: self.params[k]
            for k in self.kwdnames if k in self.params
        }

        bind('CurrentHier', self)
        ret = self.func(*func_args, **func_kwds)
        bind('CurrentHier', self.parent)

        if ret is None:
            ret = tuple()
        elif not isinstance(ret, tuple):
            ret = (ret, )

        return ret


# def func_module(cls, func, **meta_kwds):
#     @wraps(func)
#     def wrapper(*args, **kwds):
#         wrapper.meta_kwds['definition'] = wrapper.definition
#         return cls(func, meta_kwds, *args, **kwds)

#     # Add defaults from GearMetaParams registry
#     for k, v in registry('GearMetaParams').items():
#         if k not in meta_kwds:
#             meta_kwds[k] = copy.copy(v)

#     wrapper.meta_kwds = meta_kwds
#     return wrapper


def alternative(*base_gear_defs):
    def gear_decorator(gear_def):
        for d in base_gear_defs:
            alternatives = getattr(d.func, 'alternatives', [])
            alternatives.append(gear_def)
            d.func.alternatives = alternatives
        return gear_def

    return gear_decorator


# @doublewrap
# def alternative(gear_def, *args, **kwds):
#     gear_def.func.meta_kwds['alternatives'].extend(args)
#     return gear_def


@doublewrap
def gear(func, gear_cls=Gear, **meta_kwds):
    from pygears.core.funcutils import FunctionBuilder
    fb = FunctionBuilder.from_func(func)
    fb.body = (f"return gear_cls(gear_func, meta_kwds, "
               f"{fb.get_invocation_str()})")

    # Add defaults from GearExtraParams registry
    for k, v in registry('GearExtraParams').items():
        if k not in fb.kwonlyargs:
            fb.kwonlyargs.append(k)
            fb.kwonlydefaults[k] = copy.copy(v)

    # Add defaults from GearMetaParams registry
    for k, v in registry('GearMetaParams').items():
        if k not in meta_kwds:
            meta_kwds[k] = copy.copy(v)

    execdict = {'gear_cls': gear_cls, 'meta_kwds': meta_kwds, 'gear_func': func}
    execdict.update(func.__globals__)
    gear_func = fb.get_func(
        execdict=execdict)

    functools.update_wrapper(gear_func, func)

    dfn = Definition(gear_func)
    meta_kwds['definition'] = dfn
    dfn.meta_kwds = meta_kwds

    return dfn


@doublewrap
def hier(func, **meta_kwds):
    return gear(gear_cls=Hier, **meta_kwds)(func)


class HierRootPlugin(PluginBase):
    @classmethod
    def bind(cls):
        cls.registry['HierRoot'] = NamedHierNode('')
        cls.registry['CurrentHier'] = cls.registry['HierRoot']
        cls.registry['GearMetaParams'] = {
            'enablement': True
        }
        cls.registry['GearExtraParams'] = {
            'name': True,
            'intfs': [],
            'outnames': []
        }

    @classmethod
    def reset(cls):
        bind('HierRoot', NamedHierNode(''))
        bind('CurrentHier', cls.registry['HierRoot'])
