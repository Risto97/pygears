from pygears.conf import PluginBase, safe_bind

# from .bool import Bool
from .queue import Queue
from .array import Array
from .base import TemplateArgumentsError, typeof, Any, is_type
from .tuple import Tuple
from .uint import Int, Uint, Integer, Bool, Integral
from .unit import Unit
from .union import Union
from .bitw import bitw, ceil_pow2
from .tlm import TLM
from .flatten import flatten
from .expand import expand
from .factor import factor
from .fixp import Fixp, Ufixp, Fixpnumber
from .number import Number
from .float import Float

__all__ = [
    'Bool', 'Queue', 'TemplateArgumentsError', 'Tuple', 'Int', 'Uint', 'Unit',
    'Union', 'Array', 'Float', 'bitw', 'typeof', 'Any', 'TLM', 'ceil_pow2',
    'is_type', 'flatten', 'expand', 'factor', 'Ufixp', 'Fixp', 'Number',
    'Fixpnumber', 'Integral'
]


class TypingNamespacePlugin(PluginBase):
    @classmethod
    def bind(cls):
        safe_bind('gear/type_arith', {})


class CoreTypesPlugin(TypingNamespacePlugin):
    @classmethod
    def bind(cls):
        safe_bind('gear/type_arith/Union', Union)
        safe_bind('gear/type_arith/Tuple', Tuple)
        safe_bind('gear/type_arith/Uint', Uint)
        safe_bind('gear/type_arith/Float', Float)
        safe_bind('gear/type_arith/Int', Int)
        safe_bind('gear/type_arith/Integer', Integer)
        safe_bind('gear/type_arith/Integral', Integral)
        safe_bind('gear/type_arith/Unit', Unit)
        safe_bind('gear/type_arith/Fixp', Fixp)
        safe_bind('gear/type_arith/Ufixp', Ufixp)
        safe_bind('gear/type_arith/Bool', Bool)
        safe_bind('gear/type_arith/Queue', Queue)
        safe_bind('gear/type_arith/Array', Array)
        safe_bind('gear/type_arith/bitw', bitw)
        safe_bind('gear/type_arith/ceil_pow2', ceil_pow2)
        safe_bind('gear/type_arith/typeof', typeof)
        safe_bind('gear/type_arith/Any', Any)
        safe_bind('gear/type_arith/TLM', TLM)
        safe_bind('gear/type_arith/flatten', flatten)
        safe_bind('gear/type_arith/expand', expand)
        safe_bind('gear/type_arith/factor', factor)
