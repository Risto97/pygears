from pygears import alternative, gear, module
from pygears.lib import cart, ccat, fmap, permuted_apply
from pygears.typing import Int, Integer, Queue, Tuple, typeof
from pygears.util.utils import qrange, quiter

TCfg = Tuple[{
    'start': Integer['w_start'],
    'cnt': Integer['w_cnt'],
    'incr': Integer['w_incr']
}]


def rng_out_type(cfg, cnt_steps):
    if cnt_steps:
        return cfg[0] + cfg[1] + cfg[2]

    return max(cfg[0], cfg[1])


@gear(hdl={'compile': True})
async def py_rng(cfg: TCfg, *, cnt_steps=False,
                 incr_steps=False) -> Queue['rng_out_type(cfg, cnt_steps)']:

    data = module().tout.data(0)

    async with cfg as (offset, cnt, incr):
        if not cnt_steps:
            start = int(offset)
            stop = int(cnt)
            step = int(incr)
        else:
            if incr_steps:
                start = 0
                stop = int(cnt)
                step = 1
            else:
                start = int(offset)
                stop = int(offset) + int(cnt)
                step = int(incr)

        assert stop != 0, 'py_rng: range stop cannot be 0'
        assert (stop - start) % step == 0, 'py_rng: stop not reachable'

        for data, last in qrange(start, stop, step):
            if incr_steps:
                yield offset + (data * incr), last
            else:
                yield data, last


@gear(hdl={'hdl_fn': 'rng'})
async def sv_rng(cfg: TCfg,
                 *,
                 signed=b'typeof(cfg[0], Int)',
                 cnt_one_more=False,
                 cnt_steps=False,
                 incr_steps=False) -> Queue['rng_out_type(cfg, cnt_steps)']:
    def sign(x):
        return -1 if x < 0 else 1

    async with cfg as (start, cnt, incr):

        if not cnt_steps:
            rng_cfg = [int(start), int(cnt), int(incr)]
        else:
            rng_cfg = [
                int(start),
                int(start) + int(cnt) * int(incr),
                int(incr)
            ]

        rng_cfg[1] += sign(int(incr)) * cnt_one_more

        for data, last in quiter(range(*rng_cfg)):
            yield module().tout((data, last))


@gear
def rng(cfg: TCfg, *, cnt_steps=False, incr_steps=False, cnt_one_more=False):
    """Short for range, similar to python range function generates a sequence of
    numbers. The ``start``, ``cnt`` and ``incr`` fields of the :class:`Tuple`
    input type are used for the start, stop and step values.

    Args:
        cnt_steps: Whether the ``cnt`` field represents the how many steps need
          to be counted or the `stop` position for the range generator
        incr_steps: Optimization for specific cases. If set increments steps by 1
          and multiplies the final result
        cnt_one_more: If set count one value more than specified i.e. include the
          stop value

    Returns:
        A :class:`Queue` type whose data consists of the generated values and the
          `eot` signalizes the last element in the range.
    """
    any_signed = any([typeof(d, Int) for d in cfg.dtype])
    all_signed = all([typeof(d, Int) for d in cfg.dtype])
    if any_signed and not all_signed:
        cfg = cfg | fmap(f=(Int, ) * len(cfg.dtype))

    if cnt_one_more:
        return cfg | sv_rng(signed=any_signed,
                            cnt_steps=cnt_steps,
                            incr_steps=incr_steps,
                            cnt_one_more=cnt_one_more)

    return cfg | py_rng(cnt_steps=cnt_steps, incr_steps=incr_steps)


@alternative(rng)
@gear
def rng_cnt_only(cfg: Integer['w_cnt']):
    return ccat(0, cfg, 1) | rng


@alternative(rng)
@gear(enablement=b'len(cfg) == lvl')
def rng_multi_lvl(cfg: Tuple,
                  *,
                  lvl=1,
                  cnt_steps=False,
                  incr_steps=False,
                  cnt_one_more=False):
    return cfg \
        | fmap(name='forx', f=(None, rng(cnt_steps=cnt_steps,
                                         incr_steps=incr_steps,
                                         cnt_one_more=cnt_one_more)), fcat=cart) \
        | fmap(name='fory',
               f=fmap(
                   f=(rng(cnt_steps=cnt_steps,
                          incr_steps=incr_steps,
                          cnt_one_more=cnt_one_more), None),
                   fcat=permuted_apply(f=cart, indices=(1,0)))
                   # f=(rng, None), fcat=cart)
               )

    # | fmap(name='fory', f=(rng, None), lvl=2, fcat=permuted_apply(f=cart, indices=(1,0)))
