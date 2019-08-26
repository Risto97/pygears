from pygears import Intf
from pygears.lib.cart import cart
from pygears.typing import Queue, Uint, Unit
from pygears.util.test_utils import hdl_check


@hdl_check(['cart.sv', 'cart_cart_sync.sv', 'cart_cart_cat.sv'])
def test_two_queue_inputs():
    cart(Intf(Queue[Uint[4], 2]), Intf(Queue[Unit, 1]))


@hdl_check(['cart.sv', 'cart_cart_sync.sv', 'cart_cart_cat.sv'])
def test_two_inputs_first_queue():
    cart(Intf(Queue[Uint[4], 1]), Intf(Uint[1]))


@hdl_check(['cart.sv', 'cart_cart_sync.sv', 'cart_cart_cat.sv'])
def test_two_inputs_second_queue():
    cart(Intf(Uint[1]), Intf(Queue[Uint[4], 1]))
