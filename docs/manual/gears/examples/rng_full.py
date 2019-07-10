from pygears.lib import rng
from pygears.lib import shred
from pygears.lib.verif import drv
from pygears.typing import Tuple, Uint

drv(t=Tuple[Uint[2], Uint[4], Uint[2]], seq=[(2, 14, 2)]) \
    | rng \
    | shred