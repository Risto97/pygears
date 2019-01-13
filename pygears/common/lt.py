from pygears import alternative, gear

from pygears.conf import safe_bind
from pygears.core.intf import IntfOperPlugin
from pygears.typing import Tuple, Any, Uint
from . import ccat


@gear(svgen={'compile': True})
async def lt(din: Tuple[Any, Any]) -> Uint[1]:
    async with din as data:
        yield data[0] < data[1]


@alternative(lt)
@gear
def lt2(din0: Any, din1: Any):
    return ccat(din0, din1) | lt


class MulIntfOperPlugin(IntfOperPlugin):
    @classmethod
    def bind(cls):
        safe_bind('gear/intf_oper/__lt__', lt)