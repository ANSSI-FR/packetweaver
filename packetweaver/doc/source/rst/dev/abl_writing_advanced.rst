Advanced Ability Writing
========================

.. _call-abl-sync:

Using another Ability
---------------------

About the Ability Types
~~~~~~~~~~~~~~~~~~~~~~~

Simple Abilities might be self-contained, and self-sufficient. However, to
improve reusability, one might want to split code into multiple Abilities that
may or may not be run independently from the CLI.

There are actually two types of Abilities: standalone ones, and components.

A component is an Ability that can only be called from an other Ability. They
are not listed in the CLI. Conversely, a standalone Ability is listed in the CLI
and might be used by itself, although it might also be called from an other
Ability.

The type of Ability is defined with the ``type`` parameter of an ``AbilityInfo``
instance::

    from packetweaver.core.ns import *

    class ComponentAbility(AbilityBase):
        _info = AbilityInfo(name='Example', type=AbilityType.COMPONENT)
    ...
    class StandaloneAbility(AbilityBase):
        _info = AbilityInfo(name='AnotherExemple', type=AbilityType.STANDALONE)

Declaring a Dependency to another Ability
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An Ability using other Abilities must declare them as dependencies. This is done
by defining a class property called ``_dependencies``. It contains a list of
strings or tuples describing each dependency.

A string may be used when using some of the builtin Abilities from PacketWeaver. 
For instance, an Ability using the built-in Man-in-the-middle Ability, may
declare::
    class Ability(AbilityBase):
        _dependencies = [ 'mitm' ]

In the general case, though, tuples are used. Each tuple is composed of three
elements:

* the pet name that you want to use to refer to that dependency within your
  Ability;
* the name of the package (as defined in the PacketWeaver configuration file)
  that contains the Ability that your Ability relies on;
* the name of the Ability that your Ability relies on, as declared in that
  AbilityInfo name attribute.

For instance, if an Ability uses another Ability named *Test your might*
stored in the package *TestPackage*, that Ability ``_dependencies`` declaration
could be::

    _dependencies = [('mytest', 'TestPackage', 'Test your might')]

Getting an Instance of another Ability
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once an Ability declared as a dependency, you may obtain an instance of that
Ability using the built-in ``get_dependency`` method::

    class Ability(AbilityBase):
        _dependencies = [('mytest', 'TestPackage', 'Test your might')]
        def main(self):
            instance = self.get_dependency('mytest')

If the dependency has input parameters declared through a ``_option_list`` class
property, you may set them using keyword arguments, during the
``get_dependency`` call. For instance, if the *Test your might* Ability defined
a ``NumOpt`` called ``skill_level``, one could define the argument like this::

    class Ability(AbilityBase):
        _dependencies = [('mytest', 'TestPackage', 'Test your might')]
        def main(self):
            instance = self.get_dependency('mytest', skill_level=9000)

Configuring an Ability Instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parameters of Abilities that are not yet started may be set either at
instanciation time, with the keyword arguments of the ``get_dependency`` call or
by directly setting them as attributes of the object instance of that Ability.
Said otherwise, this line::

    inst = self.get_dependency('mytest', skill_level=9000)

is equivalent to::

    inst = self.get_dependency('mytest')
    inst.skill_level = 9000

.. note:: If your parameter name contains characters that are invalid for a
    Python attribute name, you may set it using ``set_opt``::
        inst.set_opt('skill_level++', 9000)

Once started, trying to alter a paramter value leads to an Exception being
raised.

Starting the Dependency
~~~~~~~~~~~~~~~~~~~~~~~

Once you have a reference to an object instance representing another Ability,
you may run it by calling the ``start`` method on it::
    
    class Ability(AbilityBase):
        _dependencies = [('mytest', 'TestPackage', 'Test your might')]
        def main(self):
            instance = self.get_dependency('mytest')
            instance.start()

If arguments are passed to the start invokation, they are passed as is to the
``main`` method of that Ability. For instance, let's assume that the *Test your
might* Ability ``main`` method is declared as::

    def main(self, arg1, arg2=True, arg3="Mighty"):

One could call that Ability with arguments like this::

    instance.start("arg1value", arg3="Weak")

Whether to use arguments with the ``start`` method or using PacketWeaver
``_option_list`` parameters is up to the Ability developer. One case where using
the ``start`` argument is convinient is when one want to pass a data type that
is not declared as a PacketWeaver option type, or when the value is an arbitrary
mutable Python object reference. In the latter case, a special argument should
be passed during ``start`` invokation, to prevent deepcopy of the parameter
value::

    instance.start({'mutable': 'array'}, deepcopy=False)

About Multi-threaded Abilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All Abilities must inherit directly or indirectly from the ``AbilityBase``
class.

Abilities inheriting directly from ``AbilityBase`` are synchronous. That means
that when started, they take control over either the CLI or the calling Ability,
and they give control back, once they are done with their tasks.

Abilities may however inherit from ``ThreadedAbilityBase`` instead of
``AbilityBase``. In that case, PacketWeaver automatically generates a thread to
handle the tasks. That means that when started, these Abilities will execute a
separate control flow. An Ability inheriting from ``ThreadedAbilityBase`` that
is run from the CLI executes until the ``main`` method returns or an unhandled
exception bubbles up. It may however call the ``_wait`` method, to wait for a
PacketWeaver stop signal. A stop signal is sent to a threaded Ability when the
*ctrl+c* control sequence is entered or when the ``stop`` method is called from
the calling Ability.

For instance, let two threaded Abilities *ABC* and *XYZ*, defined as::

    class Ability(ThreadedAbilityBase):
        _info = AbilityInfo(name='ABC', type=AbilityType.STANDALONE)
        _dependencies = [('xyz', 'MyPkg', 'XYZ')]
        def main(self):
            print "Getting instance of XYZ"
            xyz_instance = self.get_dependency('xyz')

            print "Starting XYZ"
            xyz_instance.start()
            print "Control is immediately given back here, because XYZ is threaded"

            print "Let's now wait for the stop signal from a Ctrl+C"
            self._wait()

            print "Ctrl+C received, let's propagate the stop signal to our dependencies"
            xyz_instance.stop()

            print "Let's now wait for the dependency to terminate"
            xyz_instance.join()

            return 0

    class Ability(ThreadedAbilityBase):
        _info = AbilityInfo(name='XYZ', type=AbilityType.COMPONENT)
        def main(self):
            print "Started, let's wait for the stop signal"

            self._wait()

            print "Stop signal received. Let's add some delay"
            time.sleep(10)
            return 0

The ABC example Ability gets an instance of the XYZ Ability. It starts it, waits
from a stop signal, propagates that stop signal to its instance of XYZ, waits
for it to exit, and finally exits itself.

.. note:: The ``_wait`` method is implemented using condition variables, so that
    it puts the thread to sleep without having a busy loop to check for the stop
    signal.

.. note:: To emulate ``ThreadedAbilityBase`` subclasses, classes inheriting from
    ``AbilityBase`` also implements a ``stop`` and a ``join``.

.. warning:: Ability developers should always call ``stop`` and ``join`` on
    Abilities object that they get an instance of. Even though PacketWeaver
    implements a sort of reaper that cleans up incorrectly handled
    ThreadedAbilityBase subclasses, one should always clean after themself.

When developing an Ability that subclasses ``ThreadedAbilityBase``, the "parent"
Ability may send a stop signal at any moment. While it is possible to forcefully
terminate a thread in Python, PacketWeaver Abilities should be polite and
responsive to stop signals. As such, long-blocking syscalls should be avoided
and as well as infinite loops. One should regularly check if the signal stop was
sent by calling ``self.is_stopped()``, which returns ``True`` if the current
Ability should exit as quickly as possible.

Obtaining Results
~~~~~~~~~~~~~~~~~

Ability ``main`` method may return a value. When a standalone Ability run
from the interactive CLI returns a result, the string representation of this
value is printed on console.
When a standalone or a component Ability returns a value, the ``result`` method
may be called after the ``join`` method returns.

Let a component Ability be defined as::

    import random
    from packetweaver.core.ns import *
    class Ability(AbilityBase):
        _info = AbilityInfo(name='DoSmth', type=AbilityType.COMPONENT)
        def main(self):
            return random.randint(0, 10)

The returned value may be obtained this way::

    from packetweaver.core.ns import *
    class Ability(AbilityBase):
        _info = AbilityInfo(name='main ability')
        _dependencies = [('smth', 'demo', 'DoSmth')]
        def main(self):
            inst = self.get_dependency('smth')
            inst.start()
            inst.stop()
            inst.join()
            # Now that join returned, it is safe to call result()
            self._view.success(inst.result())
 

Starting, Waiting and Stopping Multiple Abilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A helper method exists if you need to start a bunch of Abilities object, wait
for the stop signal, then propagate that stop signal to all those abilities.

This helper, called ``_start_wait_and_stop``, is a method of any ``AbilityBase``
subclass instance. It receives a list of ``AbilityBase`` subclass instances::

    inst1 = self.get_dependency('example', port=8080)
    inst2 = self.get_dependency('example', port=8081)
    self._start_wait_and_stop([inst1, inst2)

On the use of third-party libraries
-----------------------------------

Simple Abilities are self-contained and rely on the standard Python library. You
may, however, need to write some that import third-party libraries and these
third-party libraries may not be installed on every system. 

The try and forgive approach of Python means the Python module containing your
Ability must try to import the third-party libraries and an exception will be
raised if a library is unavailable. While we could live with an ImportError
exception bubbling up and killing PacketWeaver, we found that this is suboptimal
and not very user-friendly.

The traditional way of handling this situation in PacketWeaver is to try to
import the library, and set a boolean to ``True`` on success and ``False`` on
failure::

    try:
        import third_party_lib
        HAS_THIRD_PARTY_LIB = True
    except ImportError:
        HAS_THIRD_PARTY_LIB = False

This boolean may then be used in a special PacketWeaver class method called
``check_preconditions``. This class method purpose is to check for the
availability of all prerequisites for the current Ability to work. If something
is missing, this method must return a list of strings explaining in a
user-friendly way, what is broken and what needs fixing. If all preconditions
are met, an empty list must be returned. This list is notably used by the
interactive CLI to display Abilities that cannot be run in red to indicate that
some requirements are unmet. 

Here follows an example of such a ``check_preconditions`` class method::

    class Ability(...):

       @classmethod
        def check_preconditions(cls, module_factory):
            l = []
            if not HAS_THIRD_PARTY_LIB:
                l.append('Third party library XYZ support missing or broken.')
            l += super(Ability, cls).check_preconditions(module_factory)
            return l

As you can see, in this example, the class method does what is needed regarding
the current Ability, and then calls the super class method. This super class
method will work recursively across all nested Abilities that your Ability may
depend on. Thus, if any Ability that your current Ability relies on has a
missing dependency, the appropriate error messages will be displayed. It is
strongly advised to always perform this super call when you override
``check_preconditions``.

