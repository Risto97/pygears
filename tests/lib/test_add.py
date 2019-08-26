from pygears import Intf
from pygears.lib import add, directed, drv, verif
from pygears.sim import sim
from pygears.typing import Int, Tuple, Uint, Ufixp, Fixp
from pygears.util.test_utils import synth_check


def test_unsigned_overflow_cosim(tmpdir, cosim_cls):
    seq = [(0x1, 0xf), (0x2, 0xe), (0x3, 0xd)]

    verif(drv(t=Tuple[Uint[2], Uint[4]], seq=seq),
          f=add(sim_cls=cosim_cls),
          ref=add(name='ref_model'))

    sim(outdir=tmpdir)


def test_signed_unsigned_cosim(tmpdir, cosim_cls):
    seq = [(0x1, 0xf), (-0x2, 0xf), (0x1, 0x0), (-0x2, 0x0)]

    verif(drv(t=Tuple[Int[2], Uint[4]], seq=seq),
          f=add(sim_cls=cosim_cls),
          ref=add(name='ref_model'))

    sim(outdir=tmpdir)


def test_unsigned_signed_cosim(tmpdir, cosim_cls):
    seq = [(0x1, 0x7), (0x1, -0x8), (0x2, 0x7), (0x2, -0x8)]

    verif(drv(t=Tuple[Uint[2], Int[4]], seq=seq),
          f=add(sim_cls=cosim_cls),
          ref=add(name='ref_model'))

    sim(outdir=tmpdir)


def test_signed_cosim(tmpdir, cosim_cls):
    seq = [(0x1, 0x7), (-0x2, 0x7), (0x1, -0x8), (-0x2, -0x8)]

    verif(drv(t=Tuple[Int[2], Int[4]], seq=seq),
          f=add(sim_cls=cosim_cls),
          ref=add(name='ref_model'))

    sim(outdir=tmpdir)


@synth_check({'logic luts': 33}, tool='vivado')
def test_unsigned_synth_vivado():
    add(Intf(Uint[32]), Intf(Uint[32]))


@synth_check({'logic luts': 66}, tool='yosys')
def test_unsigned_synth_yosys():
    add(Intf(Uint[32]), Intf(Uint[32]))


@synth_check({'logic luts': 6}, tool='vivado')
def test_signed_unsigned_synth_vivado():
    add(Intf(Int[2]), Intf(Uint[4]))


@synth_check({'logic luts': 10}, tool='yosys')
def test_signed_unsigned_synth_yosys():
    add(Intf(Int[2]), Intf(Uint[4]))


def test_ufixp(tmpdir, sim_cls):
    directed(drv(t=Ufixp[2, 3], seq=[2.5, 0]),
             drv(t=Ufixp[3, 4], seq=[3.5, 0]),
             f=add(sim_cls=sim_cls),
             ref=[6.0, 0.0])
    sim(outdir=tmpdir)


def test_fixp(tmpdir, sim_cls):
    directed(drv(t=Fixp[2, 4], seq=[1.75, 1.75, 0, -2.0, -2.0]),
             drv(t=Fixp[3, 6], seq=[3.875, -4.0, 0, 3.875, -4.0]),
             f=add(sim_cls=sim_cls),
             ref=[5.625, -2.25, 0, 1.875, -6.0])
    sim(outdir=tmpdir)
