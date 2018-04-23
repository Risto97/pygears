from pygears.core.gear import gear
from pygears import Queue, Unit


@gear(sv_param_kwds=[], enablement=b'din_lvl >= lvl')
def quenvelope(din: Queue['din_t', 'din_lvl'], *,
               lvl) -> Queue[Unit, 'lvl']:
    """Extracts the queue structure of desired level called the envelope

    If there are more eot levels then forwarded to the output, those eot excess
levels are called subenvelope (which is not passed to the output). When
there is a subenvelope, the number of data the output transactions (envelope)
will contain is lowered by contracting each input transactions within
subenvelope to the length of 1. This is done in order that the envelope can be
correctly used within cartesian concatenations.

    """

    pass
