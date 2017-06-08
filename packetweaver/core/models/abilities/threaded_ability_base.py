import copy
import multiprocessing
import select
import threading

from packetweaver.core.models.abilities import ability_base


class ThreadedAbilityBase(threading.Thread, ability_base.AbilityBase):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        ability_base.AbilityBase.__init__(self, *args, **kwargs)
        self._stop_condition = threading.Condition()
        self._builtin_in_pipes = []
        self._builtin_out_pipes = []
        self._ret_value = None
        self._started = False

    def _wait(self):
        self._stop_condition.acquire()
        while not self.is_stopped():
            self._stop_condition.wait()
        self._stop_condition.release()

    def stop(self):
        ability_base.AbilityBase.stop(self)
        self._stop_condition.acquire()
        self._stop_condition.notify()
        self._stop_condition.release()

    def start(self, deepcopy=True, *args, **kwargs):
        # deepcopy argument is necessary in case the arguments contains stuff cannot be deep-copied
        # (some fd, for instance)
        if deepcopy:
            self._args = list(copy.deepcopy(args))
            self._kwargs = copy.deepcopy(kwargs)
        else:
            self._args = args
            self._kwargs = kwargs

        self._started = True
        threading.Thread.start(self)

    def run(self):
        try:
            self._ret_value = self.main(*self._args, **self._kwargs)
            if not self._is_source():
                for p in self._builtin_in_pipes:
                    p.close()
            if not self._is_sink():
                for out in self._builtin_out_pipes:
                    out.close()
        finally:
            self._started = False

    def result(self):
        if self._ret_value is not None:
            return self._ret_value

    def __or__(self, other):
        input, output = multiprocessing.Pipe()
        other.add_in_pipe(output)
        self.add_out_pipe(input)
        return other

    def _transfer_in(self, other):
        for p in self._builtin_in_pipes:
            other.add_in_pipe(p)
        self._builtin_in_pipes = []

    def _transfer_out(self, other):
        for out in self._builtin_out_pipes:
            other.add_out_pipe(out)
        self._builtin_out_pipes = []

    def _dup_out(self, other):
        for out in self._builtin_out_pipes:
            other.add_out_pipe(out)

    def add_in_pipe(self, p):
        if p not in self._builtin_in_pipes:
            self._builtin_in_pipes.append(p)

    def add_out_pipe(self, p):
        if p not in self._builtin_out_pipes:
            self._builtin_out_pipes.append(p)

    def is_stopped(self):
        return (
            not threading.Thread.is_alive(self)
            or ability_base.AbilityBase.is_stopped(self)
        )

    def _recv_one(self):
        while len(self._builtin_in_pipes) > 0:
            ready_to_read, _, _ = select.select(self._builtin_in_pipes, [], [])
            for p in ready_to_read:
                try:
                    msg = p.recv()
                    yield msg
                except (IOError, EOFError):
                    self._builtin_in_pipes.pop(self._builtin_in_pipes.index(p))
        raise IOError('No input pipe for this ability instance: {}'.format(type(self).get_name()))

    def _recv(self):
        if len(self._builtin_in_pipes) == 0:
            raise IOError('No input pipe for this ability instance: {}'.format(type(self).get_name()))

        try:
            return next(self._recv_gen)
        except AttributeError:
            self._recv_gen = self._recv_one()
            return next(self._recv_gen)

    def _poll(self, timeout=0.1):
        if self._is_source():
            raise IOError('No input pipe for this ability instance: {}'.format(type(self).get_name()))
        r, w, x = select.select(self._builtin_in_pipes, [], [], timeout)
        return len(r) > 0

    def _send(self, msg):
        if self._is_sink():
            raise IOError('No output pipe for this ability instance: {}'.format(type(self).get_name()))
        for out in self._builtin_out_pipes:
            try:
                out.send(msg)
            except IOError:
                self._builtin_out_pipes.pop(self._builtin_out_pipes.index(out))

    def _is_source(self):
        return len(self._builtin_in_pipes) == 0

    def _is_sink(self):
        return len(self._builtin_out_pipes) == 0
