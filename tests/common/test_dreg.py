from nose import with_setup

from pygears import clear
from pygears.cookbook.verif import directed, verif
from pygears.common.dreg import dreg
from pygears.sim import sim, timestep
from pygears.sim.modules.drv import drv
from pygears.sim.modules.verilator import SimVerilated
from pygears.typing import Uint

from utils import prepare_result_dir, skip_ifndef


@with_setup(clear)
def test_pygears_sim():
    seq = list(range(10))

    directed(drv(t=Uint[16], seq=seq), f=dreg, ref=seq)

    sim()

    assert timestep() == (len(seq) + 2)


@with_setup(clear)
def test_verilator_cosim():
    skip_ifndef('VERILATOR_ROOT')

    seq = list(range(10))
    verif(
        drv(t=Uint[16], seq=seq),
        f=dreg(sim_cls=SimVerilated),
        ref=dreg(name='ref_model'))

    sim(outdir=prepare_result_dir())


# test_verilator_cosim()
