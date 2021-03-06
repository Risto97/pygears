# from pygears import gear
# from pygears.typing import Uint
# from pygears.sim import clk, drv, seqr, sim
# from pygears.cookbook.verif import check

# from pygears.sim.extens.vcd import VCD


# def test_general():
#     @gear
#     async def priority_mux(*din: b'T') -> b'T':
#         for i, d in enumerate(din):
#             if not d.empty():
#                 async with d as item:
#                     print(f'Priority sends {item} from channel {i}')
#                     yield item
#                     print(f'Priority done')
#                     break
#         await clk()

#     @gear
#     async def f(din0: Uint['T'], din1: Uint['T'], *, skip) -> Uint['T']:
#         async with din0 as item0:
#             print(f'f got {item0} on din0')
#             for i in range(skip + 1):
#                 async with din1 as item1:
#                     print(f'f got {item1} on din1')
#                     if i == skip:
#                         yield item0 + item1
#                         print(f'f sent {item0 + item1}')

#     stim0 = seqr(t=Uint[16], seq=[10]*4) \
#         | drv

#     stim1 = seqr(t=Uint[16], seq=list(range(8))) \
#         | drv

#     (f(stim0, stim1, skip=1), stim1) \
#         | priority_mux \
#         | check(ref=[0, 11, 1, 2, 13, 3, 4, 15, 5, 6, 17, 7])

#     sim(outdir='/tmp/proba', extens=[VCD], vcd_include=['*priority*'])


# test_general()
