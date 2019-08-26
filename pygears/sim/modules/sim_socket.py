import array
import asyncio
import glob
import itertools
import logging
import math
import os
import socket
import time
from math import ceil
from subprocess import DEVNULL, Popen

import jinja2

from pygears import GearDone, bind, registry
from pygears.definitions import ROOT_DIR
from pygears.sim import clk, sim_log
from pygears.sim.modules.cosim_base import CosimBase, CosimNoData
from pygears.hdl import hdlgen
from pygears.hdl.sv.util import svgen_typedef
from pygears.typing import Uint
from pygears.util.fileio import save_file

CMD_SYS_RESET = 0x80000000
CMD_SET_DATA = 0x40000000
CMD_RESET = 0x20000000
CMD_FORWARD = 0x10000000
CMD_CYCLE = 0x08000000
CMD_READ = 0x04000000
CMD_ACK = 0x02000000


class CosimulatorStartError(Exception):
    pass


async def drive_reset(duration):
    simsoc = registry('sim/config/socket')
    await clk()
    simsoc.send_cmd(duration | CMD_SYS_RESET)
    # data = simsoc.send_req(duration | (1 << 31), Uint[4])
    for i in range(duration):
        await clk()

    # return data


def u32_repr_gen(data, dtype):
    for i in range(ceil(int(dtype) / 32)):
        yield data & 0xffffffff
        data >>= 32


def u32_repr(data, dtype):
    return array.array('I', u32_repr_gen(dtype(data).code(), dtype))


def u32_bytes_to_int(data):
    arr = array.array('I')
    arr.frombytes(data)
    val = 0
    for val32 in reversed(arr):
        val <<= 32
        val |= val32

    return val


def u32_bytes_decode(data, dtype):
    return dtype.decode(u32_bytes_to_int(data) & ((1 << int(dtype)) - 1))


j2_templates = ['runsim.j2', 'top.j2']
j2_file_names = ['run_sim.sh', 'top.sv']


def sv_cosim_gen(gear, tcp_port=1234):
    # pygearslib = util.find_spec("pygearslib")
    # if pygearslib is not None:
    #     from pygearslib import sv_src_path
    #     registry('SVGenSystemVerilogPaths').append(sv_src_path)

    outdir = registry('sim/artifacts_dir')
    if 'socket_hooks' in registry('sim/config'):
        hooks = registry('sim/config/socket_hooks')
    else:
        hooks = {}

    srcdir = os.path.join(outdir, 'src_gen')
    rtl_node = hdlgen(gear, outdir=srcdir, language='sv')
    sv_node = registry('svgen/map')[rtl_node]

    port_map = {
        port.basename: port.basename
        for port in itertools.chain(rtl_node.in_ports, rtl_node.out_ports)
    }

    structs = [
        svgen_typedef(port.dtype, f"{port.basename}")
        for port in itertools.chain(rtl_node.in_ports, rtl_node.out_ports)
    ]

    base_addr = os.path.dirname(__file__)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(base_addr),
        trim_blocks=True,
        lstrip_blocks=True)
    env.globals.update(zip=zip, int=int, print=print, issubclass=issubclass)

    context = {
        'intfs': list(sv_node.port_configs),
        'module_name': sv_node.module_name,
        'dut_name': sv_node.module_name,
        'dti_verif_path': os.path.abspath(
            os.path.join(ROOT_DIR, 'sim', 'dpi')),
        'param_map': sv_node.params,
        'structs': structs,
        'port_map': port_map,
        'out_path': os.path.abspath(outdir),
        'hooks': hooks,
        'port': tcp_port,
        'top_name': 'top',
        'activity_timeout': 1000  # in clk cycles
    }

    inc_paths = []
    context['includes'] = []
    for path in registry('hdl/include_paths'):
        inc_paths.append(path)
    inc_paths.append(srcdir)
    inc_paths.append(outdir)

    context['includes'] = [
        os.path.abspath(os.path.join(p, '*.sv')) for p in inc_paths
        if os.path.exists(p)
    ]

    # remove empty wildcard imports
    context['includes'] = [p for p in context['includes'] if glob.glob(p)]

    for templ, tname in zip(j2_templates, j2_file_names):
        res = env.get_template(templ).render(context)
        fname = save_file(tname, context['out_path'], res)
        if os.path.splitext(fname)[1] == '.sh':
            os.chmod(fname, 0o777)


class SimSocketDrv:
    def __init__(self, main, port):
        self.main = main
        self.port = port

    def reset(self):
        pass


class SimSocketInputDrv(SimSocketDrv):
    def close(self):
        self.main.sendall(b'\x00\x00\x00\x00')
        self.main.close()
        # del self.main

    def send(self, data):
        # print(f'Sending {hex(data.code())},  {repr(data)} for {self.port.basename}')
        self.main.send_cmd(CMD_SET_DATA | self.port.index)
        pkt = u32_repr(data, self.port.dtype).tobytes()
        self.main.sendall(pkt)

    def reset(self):
        self.main.send_cmd(CMD_RESET | self.port.index)

    def ready(self):
        self.main.send_cmd(CMD_READ | self.port.index)

        # import os
        # os.system("date +%s.%N")
        data = self.main.recv(4)
        # os.system("date +%s.%N")
        # print(f'Received status {data}')

        return bool(int.from_bytes(data, byteorder='little'))


class SimSocketOutputDrv(SimSocketDrv):
    def read(self):
        # print(f'Send read command for {self.index}')
        self.main.send_cmd(CMD_READ | self.index)
        data = self.main.recv(4)
        # print(f'Received status {data}')

        if int.from_bytes(data, byteorder='little'):
            buff_size = math.ceil(int(self.port.dtype) / 8)
            if buff_size < 4:
                buff_size = 4
            if buff_size % 4:
                buff_size += 4 - (buff_size % 4)

            data = self.main.recv(buff_size)
            return u32_bytes_decode(data, self.port.dtype)
        else:
            raise CosimNoData

    def reset(self):
        self.main.send_cmd(CMD_RESET | self.index)

    @property
    def index(self):
        return len(self.port.gear.in_ports) + self.port.index

    def ack(self):
        try:
            self.main.send_cmd(CMD_ACK | self.index)
        except socket.error:
            raise GearDone


class SimSocketSynchro:
    def __init__(self, main, handler):
        self.main = main
        self.handler = handler
        self.handler.settimeout(5.0)

    def cycle(self):
        self.main.send_cmd(CMD_CYCLE)

    def forward(self):
        self.main.send_cmd(CMD_FORWARD)

    back = forward

    def sendall(self, pkt):
        # print(f'Sending: {pkt}')
        self.handler.sendall(pkt)

    def recv(self, buff_size):
        return self.handler.recv(buff_size)


class SimSocket(CosimBase):
    def __init__(self,
                 gear,
                 rebuild=True,
                 run=False,
                 batch=True,
                 tcp_port=1234,
                 **kwds):
        super().__init__(gear)

        self.rebuild = rebuild

        # Create a TCP/IP socket
        self.run_cosim = run
        kwds['batch'] = batch
        self.kwds = kwds
        self.sock = None
        self.cosim_pid = None

        self.server_address = ('localhost', tcp_port)
        self.handlers = {}

        bind('sim/config/socket', self)

    def _cleanup(self):
        if self.sock:
            # sim_log().info(f'Done. Closing the socket...')
            # time.sleep(3)
            self.sock.close()
            time.sleep(1)

            if self.cosim_pid is not None:
                self.cosim_pid.terminate()

        super()._cleanup()

    def sendall(self, pkt):
        self.handlers[self.SYNCHRO_HANDLE_NAME].sendall(pkt)

    def send_cmd(self, req):
        # cmd_name = [k for k, v in globals().items() if v == (req & 0xffff0000)][0]
        # print(f'SimSocket: sending command {cmd_name}')
        pkt = req.to_bytes(4, byteorder='little')
        self.handlers[self.SYNCHRO_HANDLE_NAME].sendall(pkt)

    def recv(self, size):
        return self.handlers[self.SYNCHRO_HANDLE_NAME].recv(size)

    def send_req(self, req, dtype):
        # print('SimSocket sending request...')
        data = None

        # Send request
        pkt = req.to_bytes(4, byteorder='little')
        self.handlers[self.SYNCHRO_HANDLE_NAME].sendall(b'\x01\x00\x00\x00' +
                                                        pkt)

        # Get random data
        while data is None:
            try:
                buff_size = math.ceil(int(dtype) / 8)
                if buff_size < 4:
                    buff_size = 4
                if buff_size % 4:
                    buff_size += 4 - (buff_size % 4)
                data = self.handlers[self.SYNCHRO_HANDLE_NAME].recv(buff_size)
            except socket.error:
                sim_log().error(f'socket error on {self.SYNCHRO_HANDLE_NAME}')
                raise socket.error

        data = u32_bytes_decode(data, dtype)
        return data

    def setup(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        if os.path.exists("/tmp/socket_test.s"):
            os.remove("/tmp/socket_test.s")
        self.sock.bind("/tmp/socket_test.s")

        # Listen for incoming connections
        # self.sock.listen(len(self.gear.in_ports) + len(self.gear.out_ports))
        self.sock.listen(1)

        if self.rebuild:
            sv_cosim_gen(self.gear, self.server_address[1])

        if self.run_cosim:

            self.sock.settimeout(10)

            outdir = registry('sim/artifacts_dir')
            args = ' '.join(f'-{k} {v if not isinstance(v, bool) else ""}'
                            for k, v in self.kwds.items()
                            if not isinstance(v, bool) or v)
            if 'seed' in self.kwds:
                sim_log().warning(
                    'Separately set seed for cosimulator. Ignoring sim/rand_seed.'
                )
            else:
                args += f' -seed {registry("sim/rand_seed")}'
            if sim_log().isEnabledFor(logging.DEBUG):
                stdout = None
            else:
                stdout = DEVNULL

            sim_log().info(f'Running cosimulator with: {args}')
            self.cosim_pid = Popen(
                [f'./run_sim.sh'] + args.split(' '),
                stdout=stdout,
                stderr=stdout,
                cwd=outdir)
            time.sleep(0.1)
            ret = self.cosim_pid.poll()
            if ret is not None:
                sim_log().error(
                    f"Cosimulator error: {ret}. Check log file {outdir}/log.log"
                )
                raise CosimulatorStartError
            else:
                sim_log().info(f"Cosimulator started")

        self.loop = asyncio.get_event_loop()

        sim_log().info(f'Waiting on {self.sock.getsockname()}')

        if self.cosim_pid:
            ret = None
            while ret is None:
                try:
                    conn, addr = self.sock.accept()
                    break
                except socket.timeout:
                    ret = self.cosim_pid.poll()
                    if ret is not None:
                        sim_log().error(f"Cosimulator error: {ret}")
                        raise Exception
        else:
            sim_log().debug("Wait for connection")
            conn, addr = self.sock.accept()

        msg = conn.recv(1024)
        port_name = msg.decode()

        self.handlers[self.SYNCHRO_HANDLE_NAME] = SimSocketSynchro(self, conn)
        for p in self.gear.in_ports:
            self.handlers[p.basename] = SimSocketInputDrv(self, p)
        for p in self.gear.out_ports:
            self.handlers[p.basename] = SimSocketOutputDrv(self, p)

        sim_log().debug(f"Connection received for {port_name}")
        super().setup()
