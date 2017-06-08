# coding: utf8
import multiprocessing
import select
import socket
import ssl
import sys
import threading
import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.StrOpt(
            'cacert_file', '/etc/ssl/certs/ca-certificates.crt',
            'Path of a file containing the list of trusted CAs', optional=True
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
        ns.StrOpt('cert_file', '/etc/ssl/certs/ssl-cert-snakeoil.pem', 'Server Certificate'),
        ns.StrOpt('key_file', '/etc/ssl/private/ssl-cert-snakeoil.key', 'Server Private Key'),
        ns.ChoiceOpt('protocol', ['IPv4', 'IPv6'], comment='IPv4 or IPv6'),
        ns.IpOpt(ns.OptNames.IP_DST, '127.0.0.1', 'Binding IP'),
        ns.PortOpt(ns.OptNames.PORT_DST, 0, 'Binding Port'),
        ns.NumOpt('backlog_size', 10, 'Backlog size provided to listen()'),
        ns.NumOpt('timeout', 30, 'Timeout for sockets'),
        ns.CallbackOpt(ns.OptNames.CALLBACK, comment='Callback returning a service ability to handle a new connection'),
        ns.StrOpt('client_info_name', 'client_info',
            'Name of the service ability option that will contain the information about the client that is at the other end of the TCP connection'
        )
    ]

    _info = ns.AbilityInfo(
        name='TLS Server',
        description='Binds to a port, accept TLS connections and starts new abilities to handle them',
        authors=['Florian Maury',],
        tags=[ns.Tag.TCP_STACK_L4],
        type=ns.AbilityType.COMPONENT
    )

    def __init__(self, *args, **kwargs):
        super(Ability, self).__init__(*args, **kwargs)
        self._stop_evt = threading.Event()

    def stop(self):
        super(Ability, self).stop()
        self._stop_evt.set()

    def _accept_new_connection(self, s):
        # accepting the connection
        clt_sock, clt_info = s.accept()

        # Getting the service ability
        new_abl = self.callback()

        # Giving to the service ability the informations about the client
        new_abl.set_opt(self.client_info_name, '{}:{}'.format(clt_info[0], clt_info[1]))

        # Creating the pipes
        in_pipe_in, in_pipe_out = multiprocessing.Pipe()
        out_pipe_in, out_pipe_out = multiprocessing.Pipe()
        new_abl.add_in_pipe(in_pipe_out)
        new_abl.add_out_pipe(out_pipe_in)

        # Starting the service ability
        new_abl.start()

        return clt_sock, in_pipe_in, out_pipe_out, new_abl

    def _serve(self, server_sock):
        to_read = [server_sock]
        to_write = []
        ready_to_read = []
        ready_to_write = []
        service_abilities = []

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
                    if s is server_sock:
                        # This socket is the server_sock (the one we can run accept upon)
                        new_sock, new_in_pipe, new_out_pipe, new_abl = self._accept_new_connection(s)
                        to_read.append(new_sock)
                        to_read.append(new_out_pipe)
                        to_read.append(s)
                        to_write.append(new_sock)
                        to_write.append(new_in_pipe)
                        service_abilities.append((new_abl, new_sock, new_in_pipe, new_out_pipe))
                        ready_to_read.pop(ready_to_read.index(s))
                    else:
                        # The socket is one of the socket connected to a client

                        # StopIteration should not happen because we know that the element must be present
                        # We also know that there should be only one answer so calling on next is efficient
                        # Finally, we use a generator expression because it is more efficient (only generates up to the
                        # first matching occurrence. A list expression would have iterated over the whole list
                        abl, sock, in_pipe, out_pipe = next(
                            (srv for srv in service_abilities if s is srv[1] or s is srv[3])
                        )
                        if s is sock and in_pipe in ready_to_write:
                            try:
                                in_pipe.send(s.recv(65535))
                                to_read.append(s)
                                to_write.append(in_pipe)
                            except:
                                abl.stop()
                                sock.close()
                                in_pipe.close()
                                out_pipe.close()
                                abl.join()
                            finally:
                                ready_to_write.pop(ready_to_write.index(in_pipe))
                                ready_to_read.pop(ready_to_read.index(sock))

                        elif s is out_pipe and sock in ready_to_write:
                            try:
                                sock.send(out_pipe.recv())
                                to_read.append(out_pipe)
                                to_write.append(sock)
                            except:
                                abl.stop()
                                sock.close()
                                in_pipe.close()
                                out_pipe.close()
                                abl.join()
                            finally:
                                ready_to_write.pop(ready_to_write.index(sock))
                                ready_to_read.pop(ready_to_read.index(out_pipe))

        for abl, sock, in_pipe, out_pipe in service_abilities:
            abl.stop()
            sock.close()
            in_pipe.close()
            out_pipe.close()
            abl.join()

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
        if not isinstance(self.cacert_file, type(None)):
            ctx.load_verify_locations(cafile=self.cacert_file)

        ctx.load_cert_chain(self.cert_file, self.key_file)

        if self.protocol == 'IPv4':
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            server_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        ssl_sock = ctx.wrap_socket(server_sock, server_side=True)

        ssl_sock.bind(('' if isinstance(self.ip_dst, type(None)) else self.ip_dst, self.port_dst))

        ssl_sock.listen(self.backlog_size)
        ssl_sock.settimeout(self.timeout)

        self._serve(ssl_sock)

        try:
            server_sock = ssl_sock.unwrap()
            server_sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        finally:
            server_sock.close()
