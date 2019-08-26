"""Implements fixed width integer types: :class:`Uint` - unsigned, :class:`Int`
- signed and :class:`Integer` - sign agnostic type. These types correspond to
HDL logic vector types.

Objects of these classes can also be instantiated and they provide some integer
arithmetic capabilities.
"""

from .base import class_and_instance_method
from .base import typeof, EnumerableGenericMeta
from .number import NumberType, Number
from .tuple import Tuple
from .bitw import bitw
from .unit import Unit


class IntegralType(EnumerableGenericMeta):
    @property
    def mask(self):
        return (1 << len(self)) - 1

    @property
    def width(self):
        return int(self)

    def keys(self):
        """Returns a list of keys that can be used for indexing the type.

        >>> Int[8].keys()
        [0, 1, 2, 3, 4, 5, 6, 7]
        """
        return list(range(int(self)))

    def __getitem__(self, index):
        if not self.specified:
            return super().__getitem__(index)

        index = self.index_norm(index)

        width = 0
        for i in index:
            if isinstance(i, slice):
                if i.stop == 0 or i.start >= len(self):
                    return Unit
                elif i.stop > len(self):
                    i.stop = len(self)

                width += i.stop - i.start
            else:
                if i >= len(self):
                    raise IndexError
                width += 1

        return self.base[width]


class Integral(int, metaclass=IntegralType):
    pass


Number.register(Integral)


class IntegerType(IntegralType):
    """Defines lib methods for all Integer based classes.
    """

    def __str__(self):
        if self.args:
            if isinstance(self.args[0], int):
                return f'z{self.args[0]}'
            else:
                return f'z({self.args[0]})'
        else:
            return super().__str__()

    def __int__(self):
        if not self.__args__:
            raise TypeError

        return int(self.__args__[0])

    def __gt__(self, others):
        return int(self) > int(others)

    def __ge__(self, others):
        return int(self) >= int(others)

    def __invert__(self):
        return self

    def __neg__(self):
        return Int[int(self) + 1]

    def __or__(self, others):
        # return int(self) | int(others)
        return self.base[max(int(op) for op in (self, others))]

    def __xor__(self, others):
        return self.base[max(int(op) for op in (self, others))]

    def __lshift__(self, others):
        return self.base[int(self) + int(others)]

    def __rshift__(self, others):
        shamt = int(others)
        width = len(self)

        if shamt > width:
            raise TypeError('Right shift larger than data width')
        elif shamt == width:
            return Unit
        else:
            return self.base[width - shamt]

    def __add__(self, other):
        """Returns the same type, but one bit wider to accomodate potential overflow.

        >>> Uint[8] + Uint[8]
        Uint[9]
        """

        ops = [self, other]

        signed = any(typeof(op, Int) for op in ops)

        if signed:
            ops = [Int[int(op) + 1] if typeof(op, Uint) else op for op in ops]
            res_type = Int
        else:
            res_type = Uint

        return res_type[max(int(op) for op in ops) + 1]

    __radd__ = __add__

    def __sub__(self, other):
        """Returns the signed Int type, but one bit wider to accomodate
        potential overflow.

        >>> Uint[8] + Uint[8]
        Int[9]
        """
        ops = [self, other]

        signed = any(typeof(op, Int) for op in ops)

        if signed:
            ops = [Int[int(op) + 1] if typeof(op, Uint) else op for op in ops]
            res_type = Int
        else:
            res_type = Uint

        return res_type[max(int(op) for op in ops) + 1]

    def __mul__(self, other):
        """Returns the same type, whose width is equal to the sum of operand widths
        if both operands are unsigned.
        Returns the signed Int type if other operand is signed.

        >>> Uint[8] + Uint[8]
        Uint[16]
        >>> Uint[8] + Int[8]
        Int[16]
        """
        ops = [self, other]

        signed = any(typeof(op, Int) for op in ops)
        if signed:
            return Int[int(self) + int(other)]
        else:
            return self.base[int(self) + int(other)]

    def __truediv__(self, other):
        return self.base[int(self) - int(other) + 1]

    def __rtruediv__(self, other):
        return self.base[int(other) - int(self) + 1]

    def __floordiv__(self, other):
        return self.base[int(self) - int(other) + 1]

    def __rfloordiv__(self, other):
        return self.base[int(other) - int(self) + 1]

    def __mod__(self, other):
        return other

    def __rmod__(self, other):
        return self

    __rmul__ = __mul__

    @property
    def specified(self):
        return False


def check_width(val, width):
    if ((bitw(val) > width) and (val != 0)):
        from pygears.conf import typing_log
        breakpoint()

        typing_log().warning(
            f'Value overflow - value {val} cannot be represented with {width} bits'
        )


class Integer(Integral, metaclass=IntegerType):
    """Base type for both :class:`Int` and :class:`Uint` generic types.
    Corresponds to HDL logic vector types. For an example Integer[9] translates
    to :sv:`logic [8:0]`.
    """

    def __new__(cls, val: int = 0):
        if type(val) == cls:
            return val

        if cls.is_generic():
            res = cls[bitw(val)](int(val))
        else:
            if typeof(cls, Uint):
                res = super(Integer,
                            cls).__new__(cls,
                                         int(val) & ((1 << len(cls)) - 1))
            else:
                res = super(Integer, cls).__new__(cls, val)

        check_width(val, res.width)
        return res

    @class_and_instance_method
    @property
    def width(self):
        """Returns the number of bits used for the representation

        >>> Integer[8](0).width
        8
        """
        return len(type(self))

    @class_and_instance_method
    @property
    def mask(self):
        return (1 << self.width) - 1

    def __len__(self):
        """Returns the number of bits used for the representation

        >>> len(Integer[8](0))
        8
        """
        return self.width

    def __invert__(self):
        return type(self)(~int(self) & type(self).mask)

    def __neg__(self):
        return (-type(self))(-int(self))

    def __add__(self, other):
        if not isinstance(other, Integer):
            other = type(self).base(other)

        return (type(self) + type(other))(int(self) + int(other))

    def __sub__(self, other):
        if isinstance(other, Integer):
            return (type(self) - type(other))(int(self) - int(other))
        else:
            return type(self)(int(self) - other)

    def __mul__(self, other):
        if isinstance(other, Integer):
            return (type(self) * type(other))(int(self) * int(other))
        else:
            return type(self)(int(self) * other)

    def __str__(self):
        return f'{str(type(self))}({int(self)})'

    def __repr__(self):
        return f'{repr(type(self))}({int(self)})'

    def __int__(self):
        """Returns builtin integer type

        >>> type(int(Integer[8](0)))
        <class 'int'>
        """
        return super(Integer, self).__int__()

    @class_and_instance_method
    def __getitem__(self, index):
        """Returns the value of the indexth bit in the number representation.

        >>> Integer[8](0b10101010)[5]
        1

        >>> Integer[8](0b10101010)[1::2]
        Uint[4](15)
        """

        index = type(self).index_norm(index)

        base = None
        for i in index:
            if isinstance(i, slice):
                start, stop, _ = i.indices(self.width)

                if stop <= start:
                    part = Unit()
                else:
                    part = Uint[stop - start]((int(self)
                                               & ((1 << stop) - 1)) >> start)

            elif i < self.width:
                part = Bool(int(self) & (1 << i))
            else:
                raise IndexError

            if base is None:
                base = part
            else:
                base = part @ base

        return base

    def code(self):
        return int(self) & self.mask

    @classmethod
    def decode(cls, val):
        """Creates Integer object from any int-convertible object val.

        >>> Integer[8].decode(0xffff)
        Integer[8](255)
        """
        return cls(int(val))


class IntType(IntegerType):
    def __str__(self):
        if self.args:
            if isinstance(self.args[0], int):
                return f'i{self.args[0]}'
            else:
                return f'i({self.args[0]})'
        else:
            return super().__str__()

    @property
    def max(self):
        return self.decode(2**(self.width - 1) - 1)

    @property
    def min(self):
        return self.decode(-2**(self.width - 1))

    @property
    def specified(self):
        return IntegralType.specified.fget(self)

    @property
    def signed(self):
        return True


class Int(Integer, metaclass=IntType):
    """Fixed width generic signed integer data type.

    Generic parameters:
       N: Bit width of the :class:`Int` representation

    Args:
       val: Integer value to convert to :class:`Int`

    :class:`Int` is a generic datatype derived from :class:`Integer`. It
    represents signed integers with fixed width binary representation. Concrete
    data type is obtained by indexing:

    >>> i16 = Int[16]

    """
    __parameters__ = ['N']

    @class_and_instance_method
    @property
    def signed(self):
        return True

    def __new__(cls, val: int = 0):
        if type(val) == cls:
            return val

        if cls.is_generic():
            if isinstance(val, Uint):
                res = cls[val.width + 1](int(val))
            else:
                res = cls[val.bit_length() + 1](int(val))
        else:
            res = super(Int, cls).__new__(cls, val)
            # res = super(Int, cls).__new__(cls,
            #                               int(val) & ((1 << len(cls)) - 1))

        check_width(val, res.width if val < 0 else res.width - 1)
        return res

    def __eq__(self, other):
        return int(self) == int(other)

    @classmethod
    def decode(cls, val):
        val = int(val)
        if val >= (1 << (int(cls) - 1)):
            val -= 1 << int(cls)

        return cls(val)


class UintType(IntegerType):
    """Fixed width generic unsigned integer data type.

    Generic parameters:
       N: Bit width of the :class:`Uint` representation

    :class:`Uint` is a generic datatype derived from :class:`Integer`. It
    represents unsigned integers with fixed width binary representation.
    Concrete data type is obtained by indexing:

    >>> u16 = Uint[16]

    """

    @property
    def signed(self):
        return False

    @property
    def specified(self):
        return IntegralType.specified.fget(self)

    def __sub__(self, other):
        """Returns a Tuple of the result type and overflow bit.

        >>> Uint[16] - Uint[8]
        Tuple(Uint[16], Bool)
        """
        if (issubclass(other, Uint)):
            return Tuple[Uint[max(int(self), int(other))], Bool]
        else:
            return super().__sub__(other)

    @property
    def max(self):
        return self.decode(2**self.width - 1)

    @property
    def min(self):
        return self.decode(0)

    def __str__(self):
        if not self.args:
            return f'u'
        elif isinstance(self.args[0], int):
            return f'u{self.args[0]}'
        else:
            return f'u({self.args[0]})'


class Uint(Integer, metaclass=UintType):
    """Implements the :class:`Uint` type instance.

    Args:
       val: Integer value to convert to :class:`Uint`

    :class:`Uint` is a generic datatype derived from :class:`Integer`. It
    represents unsigned integers with fixed width binary representation.

    >>> Uint[16](0xffff)
    Uint[16](65535)

    """
    __parameters__ = ['N']

    @class_and_instance_method
    @property
    def signed(self):
        return False

    @class_and_instance_method
    def __sub__(self, other):
        if (typeof(type(other), Uint)):
            res = int(self) - int(other)
            tout = type(self) - type(other)
            return tout((res & tout[0].mask, res < 0))
        else:
            return super().__sub__(other)

    def __matmul__(self, other):
        if isinstance(other, Unit):
            return self

        if not isinstance(other, Uint):
            other = Uint(other)

        return Uint[self.width + other.width]((int(self) << other.width) +
                                              int(other))

    def __rmatmul__(self, other):
        if isinstance(other, bool):
            return Bool(other) @ self

        if isinstance(other, Unit):
            return self

        raise NotImplementedError


class BoolMeta(UintType):
    def __new__(cls, name, bases, namespace, args=[]):
        spec_cls = super().__new__(cls, name, bases, namespace, args=[1])
        return spec_cls

    def copy(self):
        return self


class Bool(Uint, metaclass=BoolMeta):
    def __new__(cls, val):
        return Uint[1](bool(val))


# Bool = Uint[1]
