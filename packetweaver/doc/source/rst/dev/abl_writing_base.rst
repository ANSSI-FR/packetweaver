.. _abl-writing-label:

Basic ability writing
=====================

.. _new-abl-base:

To write an Ability, you need to use a very short boilerplate::

    # coding: utf8
    from packetweaver.core.ns import *

    class Ability(AbilityBase):
        _info = AbilityInfo(
            name='Insert your Ability name here',
        )

        def main(self):
            # Insert your code here
            return 0

To get started, you need to:

* copy/paste that boilerplate into a Python file;
* change the name in the AbilityInfo instantiation. This must be a name unique
  to the package that contains that Ability;
* import this Python file from the ``__init__.py`` file of the package that
  contains your Ability and add a reference to your Ability class object to the ``exported_abilities``
  of the package that contains your Ability. This is described in details in
  the :ref:`configuration section <configuration-label>` of this documentation;
* stick some code into the ``main`` mathod.

To check that you got that right, you can simply have the ``main`` method
return a constant and try and run that Ability from the PacketWeaver
interactive CLI. 
For example, let's pretend that you did not change the name of the template
Ability, then you can test it like this::

    ./run_pw
    pw> list
    pw> search insert
    1 insert your Ability name here
    pw> use 1
    pw (Insert your Ability name here)> run
    0
    pw>


The above template will return 0, and this will be displayed
by the CLI, upon completion of this Ability.

.. tip:: 
    Once you have your Ability selected in the interactive CLI, remember that
    you can type the ``editor`` command to edit its source code. Every changes will
    be reloaded automatically, so that you need to type ``run`` again to see the
    result of your update.

.. warning::
    Whenever you copy/paste an existing Ability or the template Ability,
    remember to change the ``name`` value. Failing to do so will break
    PacketWeaver import mechanism


Complete the meta-data
----------------------

The Ability name is not the only information that you may set up.

Some information are just for display purposes, when you enter the ``info``
command after selecting an Ability in the interactive CLI. This is the case of:

* *description*;
* *authors*;
* *references*;
* *diffusion*;
* *reliability*.

Two other pieces of information have special purposes. 

The *tags* are a list of strings, some predefined and standard in PacketWeaver,
some custom. Any tag can be searched (and autocompleted) when using the
``search`` interactive CLI command.

The *type* values either ``AbilityType.STANDALONE`` or
``AbilityType.COMPONENT``. A component Ability is an Ability that can only be
used as part of nested Abilities. Conversely, A standalone Ability can be used
both as a component of nested Abilities, and can be run directly from the CLI.
The rationale is that you may not want to polute your Ability listing in the CLI
with all Abilities, including some that are relatively abstract and not meant to
be run directly.

Here is a complete example to illustrate them::

    _info = AbilityInfo(
        name='Ability basics',
        description='Demonstrate a basic ability',
        tags=['myproject', Tag.EXAMPLE],
        authors=['pw-team',],
        references=[['PacketWeaver online documentation', 'packetweaver.readthedocs.io'],],
        diffusion='public',
        reliability=Reliability.RELIABLE,
        type=AbilityType.STANDALONE
    )

Defined constants
^^^^^^^^^^^^^^^^^

To help building a consistent searchable database of Abilities, some constants
were defined. This is the case for the tags or the reliability information.

.. note::

    Using the built-in values is not mandatory (except for the ``type``): you
    can replace them by any string value. Just make sure that it does not make your
    Ability more difficult to find by adding tags very similar to the default ones.
    Contributors are encouraged to suggest new built-in tags.

All the built-in values are defined in the *packetweaver/core/models/status.py*
source file.

The ``howto`` method
--------------------

The ``main`` method is not the only method that is common to all Abilities and
that Ability developers are meant to override. The ``howto`` method is called by
the ``howto`` command that users may enter after selecting an Ability. While the
exact behavior is up to Ability developers, this method is meant to display
some kind of message for the user better grasp how to use the Ability they just
selected.

Feel free to provide step-by-step descriptions, to add interactions or to
provide comprehensive guidance on how to use your ability.

Adding parameters to your Ability
---------------------------------

Several types of parameters may be passed to an Ability. Parameters may be
set directly from the CLI, or they may be passed by another Ability in case of
nested Abilities.

These parameters are strongly-typed: values are automatically checked upon
assignment, with an AttributeError exception being raised if the value is
inappropriate. These parameters may also contain special values, which triggers
value generation at running time.

To add parameters to your Ability, you need to set a class property named
``_option_list`` containing, as the name implies, a list of options instances.

Here follows a example of such an option list::

    _option_list = [
        PathOpt('path', default='/bin/true', comment='mon exe', executable=True),
        PathOpt('path', default=None, comment='path to nowhere', optional=True, executable=False),
        IpOpt('mon_ip', default='RandIP', comment='mon ip'),
        IpOpt(ns.OptNames.IP_DST, default='127.0.0.1', comment='IP of the target'),
        MacOpt(ns.OptNames.MAC_SRC, default='RandMac', comment='Mac of the sender'),
        StrOpt('data', default='useful string', comment='Some data'),
        NumOpt('number', default=0, comment='A number (like port, counters...'),
        ChoiceOpt('action', ['run', 'stop', 'reboot'], comment='performed on the dstIp '),
    ]

Parameters cover various data types such as IP and MAC addresses, strings,
numbers, network cards, IP subnets, booleans, file system paths or choice
options. 

All parameter types may also contain "None", which can be assigned to parameters
that are optional.

Parameter constructors all receive a name as a first parameter. This name is
used to set and get this option value, both from the command line and from the
code.

While developing an Ability, you may obtain the current parameter value
from any method of the Ability, by accessing it as a attribute from that Ability
class instance. For instance, to access the value of a BoolOpt, representing a
boolean, called ``my_option_name``, you may simply write::

    self.my_option_name

.. note:: While parameter naming is free of constraints, you might want to use
    some of the built-in names, that are listed in the ``OptNames`` class in
    *packetweaver/core/models/status.py*. Using these names in your Ability
    creates a sense of consistency that makes the user safe.

.. warning:: Please keep in mind that if you want to access your option value using
    the attribute syntax, you need to keep your names within the boundaries of
    the Python variable naming constraints. If you want to use hyphen, spaces or
    whatever other invalid characters, you will need to access the parameter
    value using the following syntax::
        self.get_opt('my name, containing spaces and punctuation')

When reading the value of a parameter containing one of the special expressions
that generate data, the latest generated value is cached, so that multiple read
yield the same result::

    a = self.my_option_name
    b = self.my_option_name
    assert(a == b)

You may force the generation of a new value by asking for a cache bypass. For
this, there is no direct read of the attribute. Instead, you need to use the
``get_opt`` method, inherited from ``AbilityBase``::

    a = self.my_option_name
    b = self.get_opt('my_option_name', bypass_cache=True)
    assert(a != b) # Most probably different, if the RNG God is nice with us :)

Boolean parameters
^^^^^^^^^^^^^^^^^^

Booleans are represented by the ``BoolOpt`` class.

Values that can be successfully assigned to a ``BoolOpt`` are:

* ``True``;
* ``False``;
* ``"True"``;
* ``"False"``;
* ``None`` or ``"None"`` if the ``BoolOpt`` is optional.

You may define a default value using the ``default`` keyword argument, when
declaring the ``BoolOpt``::

    BoolOpt('my_bool', default=False)

The default default value is ``False``.

String parameters
^^^^^^^^^^^^^^^^^

Strings are represented by the ``StrOpt`` class.

Any string may be assigned to such a parameter, except ``"None"`` and
``RandString``. The former can be assigned when the ``StrOpt`` is
optional. The latter is a special keyword, which indicates that when
reading the parameter value, strings of random length and content must be
generated. 

As for the others, the ``default`` keyword argument enables you to define a
default value for this parameter. The default default value is ``"RandString"``.

Number parameters
^^^^^^^^^^^^^^^^^

Numbers (both integers anf floats) are represented by the ``NumOpt`` class.

Values that can be successfully assigned to a ``NumOpt`` are:

* any integer or float in Python int/float format
* any string that can be parsed by Python standard library into an integer or
  float
* ``None`` or ``"None"`` if the ``NumOpt`` is optional;
* ``"RandByte"`` to generate a random integer between 0 and 2**8;
* ``"RandSByte"`` to generate a random integer between -2**7 and 2**7 - 1;
* ``"RandShort"`` to generate a random integer between 0 and 2**16;
* ``"RandSShort"`` to generate a random integer between -2**15 and 2**15 - 1;
* ``"RandInt"`` to generate a random integer between 0 and 2**32;
* ``"RandSInt"`` to generate a random integer between -2**31 and 2**31 - 1;
* ``"RandLong"`` to generate a random integer between 0 and 2**64;
* ``"RandSLong"`` to generate a random integer between -2**63 and 2**63 - 1.

As for the others, the ``default`` keyword argument enables you to define a
default value for this parameter. The default default value is ``"RandByte"``.

IP address parameters
^^^^^^^^^^^^^^^^^^^^^

IP addresses are represented by the ``IpOpt`` class. The class may store any IP
address, be it in IPv4 or IPv6.

Values that can be successfully assigned to a ``IpOpt`` are:

* any IPv4 in quad-dotted format;
* any IPv6, compressed or uncompressed;
* ``"RandIP4"`` to generate a random IPv4 address, which might be anywhere in the
  address space, including private networks, class D and E, and loopback;
* ``"RandIP6"`` to generate completely random IPv6 address, with no guarantee that
  the address will be valid
* ``"RandIP_classA"`` to generate a random IP within the IPv4 class A
* ``"RandIP_classB"`` to generate a random IP within the IPv4 class B
* ``"RandIP_classC"`` to generate a random IP within the IPv4 class C
* ``"RandIP_classD"`` to generate a random IP within the IPv4 class D
* ``"RandIP_classE"`` to generate a random IP within the IPv4 class E

.. note:: A more complete syntax is on our TODO-list to enable you to define
    random ranges (e.g. 192.168.10-20.*).

As for the others, the ``default`` keyword argument enables you to define a
default value for this parameter. The default default value is ``"RandIP4"``.

.. warning:: ``IpOpt`` value validation are using either the Python
    ``ipaddress`` module or the ``netaddr`` module. If you do not have any of
    these, then the validation will not be performed and just about any value
    will be tolerated.

IP subnet/prefix parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^

IP prefixes are represented by the ``PrefixOpt`` class. This class may store any
IP prefix, be it in IPv4 or IPv6.

This parameter type is meant to enable you to walkthrough the prefix, by
generating each and every one IP address of the specified prefix. Generation by
either be ordered, from the first address to the last address of the prefix
(excluding the network address and the broadcast address).

As for the others, the ``default`` keyword argument enables you to define a
default value for this parameter. The default default value is
``"127.0.0.0/8"``.

This parameter constructor also has a ``ordered`` keyword argument, which values
``False`` by default. If ``True``, the generation of the IP address of the
prefix will be from the first address to the last one. If ``False`` and if
prerequisites are met, the IP address will be generated randomly inside the
prefix without ever generating the same address twice. This might come in handy
when scanning large networks, if you do not want to indirectly harass a
middlebox such as a firewall that is on path with many scanned endpoints inside
a subnet.

When all IP addresses of the specified prefix are generated, the next
cache bypass raises a ``StopIteration`` exception.

Here follows an exemple of a ``PrefixOpt`` instanciation::

    PrefixOpt('MyPrefix', default='192.0.2.0/29', ordered=True)

And the usage of such an option could be::

    try:
        while True:
            print(self.get_opt('MyPrefix', cache_bypass=True))
    except StopIteration:
        pass

.. caution:: This parameter does not work with /31 and /32 prefixes, and it
    will not work either with /127 and /128 prefixes.

.. warning:: This parameter is heavily based on the Python ``ipaddress`` or
    ``netaddr`` module, so you will need them to get anywhere with this option.
    Also, you might need the Python ``gmpy2`` module to have random IP address
    generation from this parameter.

MAC address parameters
^^^^^^^^^^^^^^^^^^^^^^

Physical addresses (MAC addresses) are represented by the ``MacOpt`` class.

Values that can be successfully assigned to a ``MacOpt`` are:

* any well-formated MAC address, as a string;
* ``"Mac00"`` as a shorthand for the null MAC address;
* ``"MacFF"`` as s shorthand for the broadcast MAC address;
* ``"RandMac"`` to generate a random MAC address;
* ``"RandMulticastMac"`` to generate a random Multicast MAC address from the
  IPv4 multicast associated MAC address range;
* ``None`` or ``"None"`` if the ``MacOpt`` is optional.

As for the others, the ``default`` keyword argument enables you to define a
default value for this parameter. The default default value is ``"RandMac"``.

Choice parameters
^^^^^^^^^^^^^^^^^

Choice parameters represent alternatives from which you can select one value.
The set of available choices is up to Ability developers, who must list them at
instanciation of the ``ChoiceOpt`` class::

    ChoiceOpt('favorite_food', ['pizza', 'beer', 'greenStuff'])

As for the others, the ``default`` keyword argument enables you to define a
default value for this parameter. The default default value is the first choice
in the specified list.

If the choice parameter is optional, the special ``"None"`` value may be
assigned too.

Port number parameters
^^^^^^^^^^^^^^^^^^^^^^

Port numbers are represented by the ``PortOpt``.

Values that can be successfully assigned to a ``PortOpt`` are:

* any port number between 0 and 65535 inclusive as a Python integer or a Python
  string;
* ``"RandPort"`` to generate a random port number between 1 and 65535 inclusive;
* ``"RandPrivilegedPort"`` to generate a random port number between 1 and 1023
  inclusive.

As for the others, the ``default`` keyword argument enables you to define a
default value for this parameter. The default default value is ``"RandPort"``.

Network card parameters
^^^^^^^^^^^^^^^^^^^^^^^

Network card names are represented by the ``NicOpt``.

Valid values for ``NicOpt`` are all network device name on the current computer,
be it the name of a network card, a bridge, a virtual Ethernet adapter, or any
other types of network devices really.

As an exception, this parameter accepts ``None`` and ``"None"`` even if this
parameter is not optionnal. The rationale is that network device
names vary between platform and distros and having a non-None default value
would break on random platforms. As such, the default default value is ``None``
and it is advised not to override it.

.. warning:: Validation of NicOpt values is performed using the Python
    ``pyroute2`` library. If this library is missing, any value will be
    accepted.

Filesystem path parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^

Filesystem paths are represented by ``PathOpt``.

Valid values for this parameter type are all strings. The valid paths may
however be constrained even further using a set of keyword arguments at
instanciation time. Here follows the list of the various constraints that may be
specified:

* ``must_exist``: if ``True``, the value must be the path of an existing file;
  if ``False``, the file must not exist at the time of check. ``None`` means
  "do not care";
* ``readable``: if ``True``, the value must be an existing file and the user
  running PacketWeaver must have read access on that file; if ``False``, the
  user running PacketWeaver must not have read access on that file. ``None``
  means "do not care";
* ``writable``: if ``True``, the value must be an existing file and the user
  running PacketWeaver must have write access on that file; if ``False``, the
  user running PacketWeaver must not have write access on that file. ``None``
  means "do not care";
* ``executable``: if ``True``, the value must be an existing file and the user
  running PacketWeaver must have execute access on that file; if ``False``, the
  user running PacketWeaver must not have execute access on that file. ``None``
  means "do not care";
* ``is_dir``: if ``True``, the path must be one of an existing directory. If
  ``False``, the path may be a directory or not.

.. warning:: ``must_exist`` is subject to race conditions. This constraint is
not for security purposes.

So, basically, if you want to create a PathOpt to write a log file, you might
want to be sure that you are not overwriting any existing file::

    PathOpt('log_file', default='/var/log/mylog.txt', must_exist=False)

.. caution:: ``must_exist=False`` is incompatible with ``readable``,
    ``writable`` and ``executable``, because the file does not exist, and does 
    not have any ACL (yet).

Text output
-----------

To help you highlight your code output, the ``_view`` object is available to
display colored messages and block structures.
Here are some examples you may use::

    self._view.success('Display in green')
    self._view.delimiter('A dashed line with title')  # with a fixed len
    self._view.delimiter()  # a dashed line with the same length
    self._view.warning('Display in yellow')
    self._view.error('Display in red')
    self._view.fail('Display in cyan')
    self._view.progress('Display in blue')
    self._view.debug('Display in purple')
    self._view.success('Display in your default terminal color')

