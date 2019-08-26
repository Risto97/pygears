from pygears.lib import accum, chop
from pygears.lib.verif import directed
from pygears.sim import sim
from pygears.sim.extens.coverage import (CoverBin, CoverGroup, CoverPoint,
                                         cover_func, CoverIterator, cover_intf)
from pygears.lib.verif import drv
from pygears.typing import Queue, Tuple, Uint
from pygears import find


def test_accum(enable_coverage=True):
    seq = [[(1, 2), (5, 2), (8, 2)], [(3, 8), (1, 8)],
           [(0, 12), (4, 12), (2, 12), (99, 12)]]
    ref = [16, 12, 117]
    t_din = Queue[Tuple[{'val': Uint[8], 'offset': Uint[8]}]]

    val_bins = [
        CoverBin('one', enablement=lambda x: x == 1, threshold=8),
        CoverBin('default')
    ]
    cross_bins = [
        CoverBin('one_two', enablement=lambda x: x[0] == 1 and x[1] == 2),
        CoverBin('three_eight', enablement=lambda x: x[0] == 3 and x[1] == 8),
        CoverBin('default')
    ]
    points = [
        CoverPoint(
            'val_cp',
            bins=val_bins,
            ignore_bins=[CoverBin('ignore', enablement=lambda x: x == 5)],
            bind_field_name='data.val',
            threshold=11),
        CoverPoint(
            'offset_cp',
            bins=None,
            dtype=Uint[8],
            bind_field_name='data.offset'),
        CoverPoint(
            'tuple_cp', bins=cross_bins, dtype=t_din[0], bind_dtype=True),
        CoverPoint(
            'qlen_cp', bins=[CoverBin('all')], bind_dtype=True, dtype=t_din)
    ]
    cg = CoverGroup('din_cg', t_din, cover_points=points)

    @cover_func(cg=cg, en=enable_coverage)
    def test_sample():
        for x in seq:
            yield x

    directed(drv(t=t_din, seq=test_sample()), f=accum, ref=ref)
    sim()
    # print(cg.report())

    # checks
    # val
    assert cg.cover_points[0].bins[0].cover_cnt == 2
    assert cg.cover_points[0].bins[1].cover_cnt == 6
    # offset
    assert cg.cover_points[1].cover_cnt == 9
    # tuple
    assert cg.cover_points[2].bins[0].cover_cnt == 1
    assert cg.cover_points[2].bins[1].cover_cnt == 1
    assert cg.cover_points[2].bins[2].cover_cnt == 7
    # qlen
    assert cg.cover_points[3].bins[0].cover_cnt == 3


def test_chop(enable_coverage=True):
    t_din = Queue[Uint[4]]
    t_size = Uint[16]

    din_cp = [
        CoverPoint('val', dtype=t_din[0], bind_dtype=True),
        CoverPoint(
            'qlen_cp', bins=[CoverBin('all')], bind_dtype=True, dtype=t_din)
    ]
    din_cg = CoverGroup('din_cg', t_din, cover_points=din_cp)
    size_cp = [
        CoverPoint(
            'size_cp',
            bins=[
                CoverBin('two', enablement=lambda x: x == 2),
                CoverBin('three', enablement=lambda x: x == 3),
                CoverBin('four', enablement=lambda x: x == 4)
            ])
    ]
    size_cg = CoverGroup('size_cg', t_size, cover_points=size_cp)
    directed(
        drv(t=t_din,
            seq=CoverIterator([list(range(9)), list(range(3))],
                              cg=din_cg,
                              en=enable_coverage)),
        drv(t=t_size, seq=CoverIterator([2, 3], cg=size_cg, en=enable_coverage)),
        f=chop,
        ref=[[0, 1], [2, 3], [4, 5], [6, 7], [8], [0, 1, 2]])
    sim()

    # print(size_cg.report())
    # print(din_cg.report())

    # size
    assert size_cg.cover_points[0].bins[0].cover_cnt == 1
    assert size_cg.cover_points[0].bins[1].cover_cnt == 1
    assert size_cg.cover_points[0].bins[2].cover_cnt == 0

    # din
    assert din_cg.cover_points[0].cover_cnt == 12
    assert din_cg.cover_points[1].bins[0].cover_cnt == 2


def test_intf(enable_coverage=True):
    t_din = Queue[Uint[4]]
    t_size = Uint[16]

    din_cp = [
        CoverPoint('val', dtype=t_din[0], bind_dtype=True),
        CoverPoint(
            'qlen_cp', bins=[CoverBin('all')], bind_dtype=True, dtype=t_din)
    ]
    din_cg = CoverGroup('din_cg', t_din, cover_points=din_cp)
    size_cp = [
        CoverPoint(
            'size_cp',
            bins=[
                CoverBin('two', enablement=lambda x: x == 2),
                CoverBin('three', enablement=lambda x: x == 3),
                CoverBin('four', enablement=lambda x: x == 4)
            ])
    ]
    size_cg = CoverGroup('size_cg', t_size, cover_points=size_cp)

    directed(
        drv(t=t_din, seq=[list(range(9)), list(range(3))]),
        drv(t=t_size, seq=[2, 3]),
        f=chop,
        ref=[[0, 1], [2, 3], [4, 5], [6, 7], [8], [0, 1, 2]])

    cover_intf(find('/chop.size').consumer, cg=size_cg)
    cover_intf(find('/chop.din').consumer, cg=din_cg)

    sim()

    # print(size_cg.report())
    # print(din_cg.report())

    # size
    assert size_cg.cover_points[0].bins[0].cover_cnt == 1
    assert size_cg.cover_points[0].bins[1].cover_cnt == 1
    assert size_cg.cover_points[0].bins[2].cover_cnt == 0

    # din
    assert din_cg.cover_points[0].cover_cnt == 12
    assert din_cg.cover_points[1].bins[0].cover_cnt == 2
