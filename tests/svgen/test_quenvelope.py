from pygears import Intf
from pygears.typing import Queue, Uint
from pygears.lib import quenvelope
from pygears.util.test_utils import hdl_check


@hdl_check(['quenvelope.sv'])
def test_skip():
    quenvelope(Intf(Queue[Uint[1], 5]), lvl=2)


@hdl_check(['quenvelope.sv'], wrapper=True)
def test_all_pass():
    quenvelope(Intf(Queue[Uint[1], 2]), lvl=2)
