from pygears import alternative, gear
from pygears.typing import Queue
from pygears.common import quenvelope, cart
from pygears.common import fmap as common_fmap


@alternative(common_fmap)
@gear(enablement=b'issubclass(din, Queue)')
def fmap(din, *, f, lvl=1, fcat=cart, balance=None, common_balance=True):
    queue_lvl = din.dtype.lvl
    fmap_lvl = min(lvl, queue_lvl)
    lvl -= fmap_lvl

    env = din | quenvelope(lvl=fmap_lvl)
    data = din[0:queue_lvl - fmap_lvl + 1]

    if lvl > 0:
        f = common_fmap(f=f, lvl=lvl, fcat=fcat, balance=balance)

    dout = data | f

    if not isinstance(dout, tuple):
        dout = (dout, )

    if balance is not None and common_balance:
        env = env | balance

    cat_dout = []
    for d in dout:
        benv = env
        if balance is not None and not common_balance:
            benv = env | balance

        cat_dout.append(fcat(benv, d))

    # Cast to remove tuple Unit from resulting cart tuple
    ret = [d | Queue[d.dtype[0][1], d.dtype.lvl] for d in cat_dout]

    return tuple(ret)
