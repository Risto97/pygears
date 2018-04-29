from pygears.typing import Integer, Tuple, Queue, Int, typeof
from pygears import gear, hier, alternative
from pygears.common import ccat, fmap


def rng_out_type(cfg, cnt_steps):
    if cnt_steps:
        return cfg[0] + cfg[1] + cfg[2]
    else:
        return max(cfg[0], cfg[1])


@gear
def sv_rng(cfg: Tuple[Integer['w_start'], Integer['w_cnt'], Integer['w_incr']],
           *,
           signed=b'typeof(cfg[0], Int)',
           cnt_one_more=False,
           cnt_steps=False,
           incr_steps=False) -> Queue['rng_out_type(cfg, cnt_steps)']:
    pass


@hier
def rng(cfg: Tuple[Integer['w_start'], Integer['w_cnt'], Integer['w_incr']],
        *,
        cnt_steps=False,
        incr_steps=False):
    signed = any([typeof(d, Int) for d in cfg.dtype])
    if signed:
        cfg = cfg | fmap(f=(Int, Int, Int))

    return cfg | sv_rng(signed=signed)


@alternative(rng)
@hier
def rng_cnt_only(cfg: Integer['w_cnt']):
    return ccat(0, cfg, 1) | rng
