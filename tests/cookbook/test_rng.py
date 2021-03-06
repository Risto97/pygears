from nose import with_setup
from nose.tools import raises

from pygears import Intf, MultiAlternativeError, clear, find
from pygears.typing import Queue, Tuple, Uint, Int
from pygears.cookbook.rng import rng, TCfg
from pygears.sim.modules.verilator import SimVerilated

from pygears.cookbook.verif import directed, verif
from pygears.sim import sim
from pygears.sim.modules.drv import drv

from utils import svgen_check, prepare_result_dir, skip_ifndef


@with_setup(clear)
def test_basic_unsigned():
    iout = rng(Intf(Tuple[Uint[4], Uint[4], Uint[2]]))

    rng_gear = find('/rng/sv_rng')

    assert iout.dtype == Queue[Uint[4]]
    assert not rng_gear.params['signed']


@with_setup(clear)
def test_basic_unsigned_sim():
    seq = [(2, 8, 2)]
    ref = [list(range(*seq[0]))]

    directed(drv(t=Tuple[Uint[4], Uint[4], Uint[2]], seq=seq), f=rng, ref=ref)

    sim(outdir=prepare_result_dir())


@with_setup(clear)
def test_basic_unsigned_cosim():
    skip_ifndef('VERILATOR_ROOT')
    seq = [(2, 8, 2)]

    verif(
        drv(t=Tuple[Uint[4], Uint[4], Uint[2]], seq=seq),
        f=rng(sim_cls=SimVerilated),
        ref=rng(name='ref_model'))

    sim(outdir=prepare_result_dir())


@with_setup(clear)
def test_basic_signed():
    iout = rng(Intf(Tuple[Int[4], Int[6], Uint[2]]))

    rng_gear = find('/rng/sv_rng')

    assert iout.dtype == Queue[Int[6]]
    assert rng_gear.params['signed']


@with_setup(clear)
def test_basic_signed_sim():
    seq = [(-15, -3, 2)]
    ref = [list(range(*seq[0]))]

    directed(drv(t=Tuple[Int[5], Int[6], Uint[2]], seq=seq), f=rng, ref=ref)

    sim(outdir=prepare_result_dir())


@with_setup(clear)
def test_basic_signed_cosim():
    skip_ifndef('VERILATOR_ROOT')
    seq = [(-15, -3, 2)]

    verif(
        drv(t=Tuple[Int[5], Int[6], Uint[2]], seq=seq),
        f=rng(sim_cls=SimVerilated),
        ref=rng(name='ref_model'))

    sim(outdir=prepare_result_dir())


@with_setup(clear)
def test_supply_constant():
    iout = rng((Uint[4](0), 8, 1))

    rng_gear = find('/rng/sv_rng')

    assert iout.dtype == Queue[Uint[4]]
    assert rng_gear.params['cfg'] == Tuple[{
        'start': Uint[4],
        'cnt': Uint[4],
        'incr': Uint[1]
    }]
    assert not rng_gear.params['signed']


@with_setup(clear)
def test_cnt_only():
    iout = rng(8)

    assert iout.dtype == Queue[Uint[4]]

    rng_gear = find('/rng/rng/sv_rng')
    assert rng_gear.params['cfg'] == Tuple[Uint[1], Uint[4], Uint[1]]


@with_setup(clear)
def test_cnt_only_sim():
    seq = [8]
    ref = [list(range(8))]

    directed(drv(t=Uint[4], seq=seq), f=rng, ref=ref)

    sim(outdir=prepare_result_dir())


@with_setup(clear)
def test_cnt_only_cosim():
    skip_ifndef('VERILATOR_ROOT')
    seq = [8]

    verif(
        drv(t=Uint[4], seq=seq),
        f=rng(sim_cls=SimVerilated),
        ref=rng(name='ref_model'))

    sim(outdir=prepare_result_dir())


@with_setup(clear)
def test_cnt_down():
    iout = rng((7, 0, -1))

    rng_gear = find('/rng/sv_rng')

    assert rng_gear.params['signed']
    assert rng_gear.params['cfg'] == Tuple[Int[4], Int[2], Int[1]]
    assert iout.dtype == Queue[Int[4]]


@raises(MultiAlternativeError)
@with_setup(clear)
def test_multi_lvl():
    iout = rng((1, 2, 3), lvl=2)
    print(iout.dtype)


@with_setup(clear)
@svgen_check(['rng_hier.sv'])
def test_basic_unsigned_svgen():
    rng(Intf(Tuple[Uint[4], Uint[2], Uint[2]]))


@with_setup(clear)
@svgen_check(['rng_rng.sv', 'rng_ccat.sv', 'rng_hier.sv'])
def test_cnt_svgen():
    rng(8)
