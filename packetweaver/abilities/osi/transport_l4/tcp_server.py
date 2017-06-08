# coding: utf8
import multiprocessing
import select
import socket
import threading
import packetweaver.core.ns as ns


class Ability(ns.ThreadedAbilityBase):
    _option_list = [
        ns.ChoiceOpt('protocol', ['IPv4', 'IPv6'], comment='IPv4 or IPv6'),
        ns.IpOpt(ns.OptNames.IP_DST, '127.0.0.1', 'Binding IP'),
        ns.PortOpt(ns.OptNames.PORT_DST, 0, 'Binding Port'),
        ns.NumOpt('backlog_size', 10, 'Backlog size provided to listen()'),
        ns.NumOpt('timeout', 30, 'Timeout for sockets'),
        ns.CallbackOpt(ns.OptNames.CALLBACK, comment='Callback returning an ability to handle a new connection'),
        ns.StrOpt('client_info_name', None,
            'Name of the service ability option that will contain the information about the client that is at the other end of the TCP connection',
            optional=True
        )
    ]

    _info = ns.AbilityInfo(
        name='TCP Server',
        description='Binds to a port, accept connections and starts new abilities to handle them',
        authors=['Florian Maury', ],
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

        # Giving to the service ability the information about the client
        if not isinstance(self.client_info_name, type(None)):
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
        if self.protocol == 'IPv4':
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            server_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        server_sock.bind(('' if isinstance(self.ip_dst, type(None)) else self.ip_dst, self.port_dst))

        server_sock.listen(self.backlog_size)
        server_sock.settimeout(self.timeout)

        self._serve(server_sock)

        server_sock.close()
