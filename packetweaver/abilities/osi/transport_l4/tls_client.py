# coding: utf8
import select
import socket
import ssl
import sys
import threading
import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.StrOpt(
            'cacert_file', '/etc/ssl/certs/ca-certificates.crt', 'Path of a file containing the list of trusted CAs'
        ),
        ns.StrOpt('alpn', None, 'Application-Layer Protocol Negotiation value (as a CSV)', optional=True),
        ns.StrOpt('cipher_suites', ':'.join([  # List from ANSSI TLS guide v.1.1 p.51
                'ECDHE-ECDSA-AES256-GCM-SHA384',
                'ECDHE-RSA-AES256-GCM-SHA384',
                'ECDHE-ECDSA-AES128-GCM-SHA256',
                'ECDHE-RSA-AES128-GCM-SHA256',
                'ECDHE-ECDSA-AES256-SHA384',
                'ECDHE-RSA-AES256-SHA384',
                'ECDHE-ECDSA-AES128-SHA256',
                'ECDHE-RSA-AES128-SHA256',
                'ECDHE-ECDSA-CAMELLIA256-SHA384',
                'ECDHE-RSA-CAMELLIA256-SHA384',
                'ECDHE-ECDSA-CAMELLIA128-SHA256',
                'ECDHE-RSA-CAMELLIA128-SHA256',
                'DHE-RSA-AES256-GCM-SHA384',
                'DHE-RSA-AES128-GCM-SHA256',
                'DHE-RSA-AES256-SHA256',
                'DHE-RSA-AES128-SHA256',
                'AES256-GCM-SHA384',
                'AES128-GCM-SHA256',
                'AES256-SHA256',
                'AES128-SHA256',
                'CAMELLIA128-SHA256'
            ]), 'Proposed Ordered Cipher Suite List'),
        ns.BoolOpt('compress', False, 'Should TLS compression be used?'),
        ns.ChoiceOpt(
            'version', ['SSLv3', 'TLSv1', 'TLSv1.1', 'TLSv1.2'], default='TLSv1.2', comment='SSL/TLS protocol version',
        ),
        ns.StrOpt('cert_file', None, 'Client Certificate', optional=True),  # To be set only in case of mutual authn
        ns.StrOpt('key_file', None, 'Client Private Key', optional=True),  # To be set only in case of mutual authn
        ns.ChoiceOpt('protocol', ['IPv4', 'IPv6'], comment='IPv4 or IPv6'),
        ns.IpOpt(ns.OptNames.IP_SRC, None, 'Local (Source) IP', optional=True),
        ns.IpOpt(ns.OptNames.IP_DST, '127.0.0.1', 'Remote (Destination) IP'),
        ns.StrOpt('hostname', None, 'Remote Name (dnsName)', optional=True),
        ns.PortOpt(ns.OptNames.PORT_SRC, 0, 'Local (Source) Port (0 = Random Port)'),
        ns.PortOpt(ns.OptNames.PORT_DST, 0, 'Remote (Destination) Port'),
        ns.OptionTemplateEntry(lambda x: 0 <= x <= 10, ns.NumOpt('timeout', 5, 'Connect Timeout'))
    ]

    _info = ns.AbilityInfo(
        name='TLS Client',
        description='Connects then sends and receives TLS records',
        authors=['Florian Maury'],
        tags=[ns.Tag.TCP_STACK_L4],
        type=ns.AbilityType.COMPONENT
    )

    def __init__(self, *args, **kwargs):
        super(Ability, self).__init__(*args, **kwargs)
        self._stop_evt = threading.Event()

    def stop(self):
        super(Ability, self).stop()
        self._stop_evt.set()

    def _serve(self, ssl_sock):
        to_read = [ssl_sock] + self._builtin_in_pipes
        to_write = [ssl_sock] + self._builtin_out_pipes
        ready_to_read = []
        ready_to_write = []

        while not self._stop_evt.is_set():
            # Waiting for sockets to be ready
            readable, writable, errored = select.select(to_read, to_write, [], 0.1)
            # Adding the sockets that are ready to the list of the already ready sockets
            ready_to_write += writable
            to_write = [x for x in to_write if x not in ready_to_write]
            ready_to_read += readable
            to_read = [x for x in to_read if x not in ready_to_read]

            if len(ready_to_read) > 0:
                # For each socket that is ready to be read
                for s in ready_to_read:
                    if s is ssl_sock and all([out in ready_to_write for out in self._builtin_out_pipes]):
                        try:
                            msg = ssl_sock.recv(65535)
                            if len(msg) == 0:
                                raise EOFError
                            self._send(msg)
                            to_read.append(ssl_sock)
                            to_write += self._builtin_out_pipes
                        except:
                            self.stop()
                        finally:
                            ready_to_read.pop(ready_to_read.index(s))
                            for out in self._builtin_out_pipes:
                                ready_to_write.pop(ready_to_write.index(out))
                    elif s in self._builtin_in_pipes and ssl_sock in ready_to_write:
                        try:
                            ssl_sock.send(self._recv())
                            to_read += self._builtin_in_pipes
                            to_write.append(ssl_sock)
                        except:
                            self.stop()
                        finally:
                            for p in self._builtin_in_pipes:
                                ready_to_read.pop(ready_to_read.index(p))
                            ready_to_write.pop(ready_to_write.index(ssl_sock))

    def main(self):
        # Check Python version
        py_ver = sys.version_info
        if (
            py_ver.major < 2
            or (
                py_ver.major == 2
                and (
                    py_ver.minor < 7
                    or (py_ver.minor >= 7 and py_ver.micro < 10)
                )
            )
        ):
            raise Exception('Your version of Python and Python-ssl are too old. Please upgrade to more "current" versions')

        if self._is_sink() or self._is_source():
            raise Exception('This ability must be connected through pipes to other abilities!')

        # Set up SSL/TLS context
        tls_version_table = {
            'SSLv3': ssl.PROTOCOL_SSLv23,
            'TLSv1': ssl.PROTOCOL_TLSv1,
            'TLSv1.1': ssl.PROTOCOL_TLSv1_1,
            'TLSv1.2': ssl.PROTOCOL_TLSv1_2,
        }

        tls_version = tls_version_table[self.version]

        ctx = ssl.SSLContext(tls_version)
        if not isinstance(self.alpn, type(None)):
            ctx.set_alpn_protocols(','.join(self.alpn))
        ctx.set_ciphers(self.cipher_suites)
        ctx.load_verify_locations(cafile=self.cacert_file)

        if isinstance(self.key_file, type(None)) ^ isinstance(self.cert_file, type(None)):
            raise Exception('Both key_file and cert_file must be set or none of them.')
        if not isinstance(self.key_file, type(None)):
            ctx.load_cert_chain(self.cert_file, self.key_file)

        if self.protocol == 'IPv4':
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        if isinstance(self.hostname, type(None)):
            ssl_sock = ctx.wrap_socket(s)
        else:
            ssl_sock = ctx.wrap_socket(s, server_hostname=self.hostname)

        ssl_sock.bind(('' if isinstance(self.ip_src, type(None)) else self.ip_src, self.port_src))
        ssl_sock.connect((self.ip_dst, self.port_dst))

        self._serve(ssl_sock)

        try:
            s = ssl_sock.unwrap()
            s.shutdown(socket.SHUT_RDWR)
        except:
            pass
        finally:
            s.close()
