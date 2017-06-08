.. _abl-orchestration-label:

Flow-based Programming and Ability writing
==========================================

Abilities might be run in parallel, using ``ThreadedAbilityBase`` subclasses.
Yet, they run unbeknownst to each other, save for the parent Ability that know
them all.

PacketWeaver offers syntactic sugars for you to write Abilities that communicate
with each others, improving on the classic shell pipe syntax.

Doing it all by hand
~~~~~~~~~~~~~~~~~~~~

You may add by hand input and output pipes to any ThreadedAbilityBase subclass
instance. These pipes are ``multiprocessing.Pipe`` instances. As such, adding
such pipes may be done like this::

    inst = self.get_dependency('example')
    outputp, inputp = multiprocessing.Pipe()
    outputp2, inputp2 = multiprocessing.Pipe()
    inst.add_in_pipe(inputp)
    inst.add_out_pipe(outputp2)

    self._start_wait_and_stop([inst])

Once set up like this, the parent Ability may write into ``outputp`` and read
from ``inputp2``.

.. warning:: you cannot add pipes to an already started Abilitya hitherto.

Reading and writing from an Ability
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reading
^^^^^^^

For the point of view of the Ability refered to by the pet name *example*, input
data may be read from the *standard input* by calling the built-in ``_recv()``
instance method::

    def main(self):
       p = self._recv()

The ``_recv`` method consumes the input data as datagrams, not streams.
Moreover, you may receive all types of pickable data, which means that in the
previous example, ``p`` might be a full-fledged Python object!

.. warning:: the ``_recv`` method is blocking, kernel-wise. This is a problem
    because well-written Abilities must keep aware of the stop signal. For this
    reason, the standard way of reading the *standard input* of an Ability is to
    write a code similar to this one::
    
        def main(self):
            try:
                while not self._is_stopped():
                    if self._poll(0.1):
                        p = self._recv()
                        # Do something with p
            except (EOFError, IOError):
                pass

The ``_poll`` method is similar to the Kernel poll syscall. It monitors whether
there is a datagram to be read on the standard input, and it times out after a
certain delay (100 miliseconds in the previous example). The previous example
code thus ensures that this Ability checks at least every 100 ms that a stop
signal was received.

Writing
~~~~~~~

Writing to the *standard output* of an Ability is relatively simple. You may
simply call the ``_send`` method with any Pickable Python object as argument::

    def main(self):
        self._send('abc')

.. caution:: ``_send`` might be blocking at times, which is in violations of the
    code of conduct of well-written Abilities... This is a known limitation.

Using the Pipe Syntactic Sugar
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Whenever an Ability purpose is to orchestrate multiple Abilities, it owns the
references to multiple Abilities objects::

    inst1 = self.get_dependency('example1')
    inst2 = self.get_dependency('example2')
    inst3 = self.get_dependency('example3')

Configuring the pipes between these Abilities by hand might be cumbersome. For
this reason, PacketWeaver ships a syntactic sugar similar to shell pipes.

To pipe the *standard output* of the first Ability to the standard input of the
second Ability, one can write the following Python expression::

    inst1 | inst2

We use the fluent design pattern, so that one may write::

    inst1 | inst2 | inst3 | inst1

.. note:: In the previous example, ``inst1`` is listed twice into the pipeline.
    This is the same instance of the same Ability. This line means that the
    *standard output* of ``inst1`` is piped into ``inst2``, and that the *standard
    output* of ``inst3`` is piped into the *standard input* of ``inst1``. This
    enables developers to write pipelines of Abilities that are cyclic in a
    much easier way that it is generally possible in shell (e.g. *netcat*
    pipelines with named FIFOs)

Multiple Inputs and Outputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

While in shell, it is possible to pipe multiple scripts output into a script
standard input, it requires some tricks, for instance using named FIFOs. With
Packetweaver, multiple inputs and multiple outputs are seemless::

    def main(self):
        inst1 = self.get_dependency('example1')
        inst2 = self.get_dependency('example2')
        inst3 = self.get_dependency('example3')
        inst4 = self.get_dependency('example4')
        inst5 = self.get_dependency('example5')

        inst1 | inst2 | inst3
        inst4 | inst2 | inst5

        self._start_wait_and_stop([inst1, inst2, inst3, inst4, inst5])

In the previous example, ``inst2`` is part of two pipeline declarations. However
Packetweaver interprets this as: ``inst2`` standard input is composed of a
**round robin read** from ``inst1`` and ``inst4``, and ``inst2`` standard output
is broadcast to ``inst3`` and ``inst5``.
    

On Detecting Source and Sink Conditions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An Ability may dynamically discover if there are other Abilities that are piped
to its standard input by calling ``self._is_source()``. If ``True``, this
Ability has currently no input pipes.

Similarly, an Ability may discover if other Abilities subscribed to its standard
output by calling ``self._is_sink()``.

Transfering Pipes
~~~~~~~~~~~~~~~~~

Sometimes, the sole purpose of some component Abilities is to instanciate other
component Abilities and set up the pipelines. If that orchestrating Ability has
standard input and standard output pipes, it would be cumbersome to transfer by
hand all input and output messages to the pipeline. For this reason,
Packetweaver enables an Ability developer to specify that all input or output
pipes are to be transfered from the current Ability to another Ability. This is
performed using the ``self._transfer_in(otherAbilityInstance)`` and
``self._transfer_out(otherAbilityInstance)`` methods.

The following Ability sets up such a pipeline::

    def main(self):
        inst1 = self.get_dependency('example1')
        inst2 = self.get_dependency('example2')
        inst3 = self.get_dependency('example3')
        
        inst1 | inst2 | inst3

        self._transfer_in(inst1)
        self._transfer_out(inst3)

        self._start_wait_and_stop([inst1, inst2, inst3])
