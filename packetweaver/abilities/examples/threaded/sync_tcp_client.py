# coding: utf8
from packetweaver.core.ns import *


class Ability(AbilityBase):

    _info = AbilityInfo(
        name='TCP sync server',
        description='use the tcp_client ability to simply send data over tcp in a synchronous way',
    )

    _option_list = [
        PortOpt(OptNames.PORT_DST, 2222, 'listening port on the TCP server'),
        IpOpt(OptNames.IP_DST, '127.0.0.1', 'server IP address'),
        StrOpt('msg', 'Hello from PacketWeaver\n', 'Message to send over TCP')
    ]

    _dependencies = ['tcpclnt']

    def main(self):
        inst = self.get_dependency('tcpclnt', protocol='IPv4', ip_dst=self.ip_dst, port_dst=self.port_dst)

        to_tcp, out_pipe = multiprocessing.Pipe()
        out_pipe_2, from_tcp = multiprocessing.Pipe()
        inst.add_in_pipe(out_pipe)
        inst.add_out_pipe(out_pipe_2)

        self._view.debug('Starting tcpclnt')
        inst.start()

        self._view.debug('Send msg')
        to_tcp.send(self.msg)
        r = from_tcp.recv()
        self._view.info('{}'.format(r))

        self._view.debug('Stop tcpclnt')
        inst.stop()
        inst.join()
        self._view.success('All done')

    def howto(self):
        self._view.delimiter('TCP synchronous server')
        self._view.info("""
        A simple ability that connect to a TCP server, send 
        a string and await for a response.
        
        It can easily be tested against a netcat emulated server:
        1. the command "nc -lp 2222" will listen to the port 2222
        2. running the ability in another terminal will write your 
            message to the netcat output
        3. writing a short text in the netcat view will send back 
            a message, terminating the ability
        
        """)
