from pygears import gear, module, cast as type_cast
from pygears.conf import safe_bind
from pygears.core.intf import IntfOperPlugin
from pygears.rtl.connect import rtl_connect
from pygears.rtl.gear import RTLGearHierVisitor
from pygears.rtl import flow_visitor, RTLPlugin
from pygears.hdl.sv import SVGenPlugin
from pygears.hdl.v import VGenPlugin


@gear(hdl={'compile': True})
async def cast(din, *, cast_type) -> b'type_cast(din, cast_type)':
    async with din as d:
        yield type_cast(d, cast_type)


def pipe(self, other):
    if self.producer is not None:
        name = f'cast_{self.producer.basename}'
    else:
        name = 'cast'

    return cast(self, cast_type=other, name=name)


@flow_visitor
class RemoveEqualReprCastVisitor(RTLGearHierVisitor):
    def cast(self, node):
        pout = node.out_ports[0]
        pin = node.in_ports[0]

        if int(pin.dtype) == int(pout.dtype):
            node.bypass()


class RTLCastPlugin(IntfOperPlugin, VGenPlugin, SVGenPlugin):
    @classmethod
    def bind(cls):
        safe_bind('gear/intf_oper/__or__', pipe)
        cls.registry['vgen']['flow'].insert(0, RemoveEqualReprCastVisitor)
        cls.registry['svgen']['flow'].insert(0, RemoveEqualReprCastVisitor)
