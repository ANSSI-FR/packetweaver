import copy
import multiprocessing
import select
import threading
import logging

from packetweaver.core.models.abilities import ability_base


class ThreadedAbilityBase(threading.Thread, ability_base.AbilityBase):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        ability_base.AbilityBase.__init__(self, *args, **kwargs)
        self._stop_condition = threading.Condition()
        self._builtin_in_pipes = []
        self._builtin_out_pipes = []
        self._ret_value = None
        self._started_status = False
        self.logger = logging.getLogger(__name__)

    def _wait(self):
        self.logger.debug('[{}] waiting'.format(self._info.get_name()))
        with self._stop_condition:
            while not self.is_stopped():
                self._stop_condition.wait()
        self.logger.debug('[{}] leave wait'.format(self._info.get_name()))

    def stop(self):
        ability_base.AbilityBase.stop(self)
        with self._stop_condition:
            self._stop_condition.notify()
            self.logger.debug('[{}] stop notified'.format(self._info.get_name()))

    def start(self, deepcopy=True, *args, **kwargs):
        # deepcopy argument is necessary in case the arguments contains stuff cannot be deep-copied
        # (some fd, for instance)
        if deepcopy:
            self.logger.debug('[{}] deep copy params'.format(self._info.get_name()))
            self._args = list(copy.deepcopy(args))
            self._kwargs = copy.deepcopy(kwargs)
        else:
            self.logger.debug('[{}] straight use of params'.format(self._info.get_name()))
            self._args = args
            self._kwargs = kwargs

        self._started_status = True
        self.logger.debug('[{}] running thread'.format(self._info.get_name()))
        threading.Thread.start(self)

    def run(self):
        try:
            self.logger.debug('[{}] starting main'.format(self._info.get_name()))
            self._ret_value = self.main(*self._args, **self._kwargs)
            self.logger.debug('[{}] end of main'.format(self._info.get_name()))
            if not self._is_source():
                self.logger.debug(
                    '[{}] is source, closing {} builtin_in_pipes'.format(
                        self._info.get_name(),
                        len(self._builtin_in_pipes)))
                for p in self._builtin_in_pipes:
                    p.close()
            if not self._is_sink():
                self.logger.debug(
                    '[{}] has sunk, closing {} builtin_out_pipes'.format(
                        self._info.get_name(),
                        len(self._builtin_out_pipes)))
                for out in self._builtin_out_pipes:
                    out.close()
        finally:
            self._started_status = False

    def result(self):
        if self._ret_value is not None:
            return self._ret_value

    def __or__(self, other):
        self.logger.debug('[{}] new out pipe to [{}]'.format(self._info.get_name(), other._info.get_name()))
        input, output = multiprocessing.Pipe()
        other.add_in_pipe(output)
        self.add_out_pipe(input)
        return other

    def _transfer_in(self, other):
        self.logger.debug('[{}] transfer {} in pipes to [{}]'.format(
            self._info.get_name(),
            len(self._builtin_in_pipes),
            other._info.get_name())
        )
        for p in self._builtin_in_pipes:
            other.add_in_pipe(p)
        self._builtin_in_pipes = []

    def _transfer_out(self, other):
        self.logger.debug('[{}] transfer {} out pipes to [{}]'.format(
            self._info.get_name(),
            len(self._builtin_out_pipes),
            other._info.get_name())
        )
        for out in self._builtin_out_pipes:
            other.add_out_pipe(out)
        self._builtin_out_pipes = []

    def _dup_out(self, other):
        for out in self._builtin_out_pipes:
            other.add_out_pipe(out)

    def add_in_pipe(self, p):
        if p not in self._builtin_in_pipes:
            self._builtin_in_pipes.append(p)
        self.logger.debug('[{}] has {} in pipe'.format(
            self._info.get_name(),
            len(self._builtin_in_pipes))
        )

    def add_out_pipe(self, p):
        if p not in self._builtin_out_pipes:
            self._builtin_out_pipes.append(p)
        self.logger.debug('[{}] has {} out pipe'.format(
            self._info.get_name(),
            len(self._builtin_out_pipes))
        )

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
