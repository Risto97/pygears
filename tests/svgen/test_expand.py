from nose import with_setup

from pygears import Intf, clear
from pygears.typing import Union, Uint, Tuple
from pygears.common.expand import expand

from utils import svgen_check


@with_setup(clear)
@svgen_check([])
def test_tuple_union():
    a = Tuple[Union[Uint[2], Uint[3]],
              Union[Uint[10], Uint[11], Uint[12]],
              Tuple[Uint[8], Uint[8]],
              Union[Uint[7], Uint[8]]]
    iout = expand(Intf(a))
