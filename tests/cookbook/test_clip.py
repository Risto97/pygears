import random
from functools import partial

from nose import with_setup

from pygears import clear
from pygears.cookbook.clip import clip
from pygears.cookbook.verif import directed, verif
from pygears.sim import sim
from pygears.sim.extens.randomization import create_constraint, rand_seq
from pygears.sim.extens.svrand import SVRandSocket
from pygears.sim.modules.drv import drv
from pygears.sim.modules.sim_socket import SimSocket
from pygears.sim.modules.verilator import SimVerilated
from pygears.typing import Queue, Uint
from utils import prepare_result_dir, skip_ifndef

t_din = Queue[Uint[16]]
t_cfg = Uint[16]


def get_stim():
    cfg_seq = []
    din_seq = []
    cfg_num = random.randint(2, 10)
    for i in range(cfg_num):
        cfg_seq.append(random.randint(1, 10))
        din_seq.append(list(range(random.randint(1, 10))))

    return [drv(t=t_din, seq=din_seq), drv(t=t_cfg, seq=cfg_seq)]


@with_setup(clear)
def test_pygears_sim():
    directed(
        drv(t=t_din, seq=[list(range(9)), list(range(5))]),
        drv(t=t_cfg, seq=[2, 3]),
        f=clip,
        ref=[[0, 1],
             list(range(2, 9)),
             list(range(3)),
             list(range(3, 5))])

    sim()


@with_setup(clear)
def test_pygears_sim_stop():
    directed(
        drv(t=t_din, seq=[list(range(9)), list(range(5))]),
        drv(t=t_cfg, seq=[2, 3]),
        f=clip(clip_stop=1),
        ref=[[0, 1], list(range(3))])

    sim()


def verilator_cosim(clip_stop):
    skip_ifndef('VERILATOR_ROOT')
    stim = get_stim()
    verif(
        *stim,
        f=clip(sim_cls=SimVerilated, clip_stop=clip_stop),
        ref=clip(name='ref_model', clip_stop=clip_stop))
    sim(outdir=prepare_result_dir())


@with_setup(clear)
def test_verilator_cosim():
    verilator_cosim(clip_stop=0)


# @with_setup(clear)
# def test_verilator_cosim_stop():
#     verilator_cosim(clip_stop=1)


def socket_cosim(clip_stop):
    skip_ifndef('SIM_SOCKET_TEST')
    stim = get_stim()
    verif(
        *stim,
        f=clip(sim_cls=partial(SimSocket, run=True), clip_stop=clip_stop),
        ref=clip(name='ref_model', clip_stop=clip_stop))
    sim(outdir=prepare_result_dir())


@with_setup(clear)
def test_socket_cosim():
    socket_cosim(clip_stop=0)


@with_setup(clear)
def test_socket_cosim_stop():
    socket_cosim(clip_stop=1)


def socket_cosim_rand(clip_stop):
    skip_ifndef('SIM_SOCKET_TEST')

    cnt = 5
    cons = []
    cons.append(create_constraint(t_din, 'din', eot_cons=['data_size == 20']))
    cons.append(create_constraint(t_cfg, 'cfg', cons=['cfg < 20', 'cfg > 0']))

    stim = []
    stim.append(drv(t=t_din, seq=rand_seq('din', cnt)))
    stim.append(drv(t=t_cfg, seq=rand_seq('cfg', cnt)))

    verif(
        *stim,
        f=clip(sim_cls=partial(SimSocket, run=True), clip_stop=clip_stop),
        ref=clip(name='ref_model', clip_stop=clip_stop))

    sim(outdir=prepare_result_dir(), extens=[partial(SVRandSocket, cons=cons)])


@with_setup(clear)
def test_socket_cosim_rand():
    socket_cosim_rand(clip_stop=0)


@with_setup(clear)
def test_socket_cosim_rand_stop():
    socket_cosim_rand(clip_stop=1)
