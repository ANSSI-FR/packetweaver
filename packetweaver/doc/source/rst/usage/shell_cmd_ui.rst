Shell and interactive command line
==================================

PacketWeaver gives you two ways of interacting with your Abilities (see :ref:`Introduction <intro-label>` for explanations).

The pw interactive CLI
----------------------

The interactive CLI is the main way of interacting with the framework. It is
composed of two levels: one that enables you to browse and to select available
Abilities, and another one to configure and run a selected Ability.

The interactive CLI offers command history features similar to that of usual
shells, such as history search and command recall, using ``ctrl+p``, ``ctrl+n``
and ``ctrl+r``.

To cancel a command, you may use ``ctrl+c``. ``ctrl+d`` and ``exit`` may be
used to return to unselect an Ability, or exit the framework. Finally, ``tab``
can be used to trigger autocompletion of the current command line, whenever
available.

.. _shell-interface-lvl1-label:

Ability browsing and selection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To launch the interactive CLI, you may run the ``run_pw`` script located at the
root of the PacketWeaver git repository::

    ./run_pw

This CLI understands a bunch of commands whose list you can obtain by typing
the ``help`` command or ``?`` for short. Help of any of the listed commands can
be obtained by using the ``help`` command followed by the name of a command::

    pw> help list

For instance, the ``list`` command displays a list of all the available standalone
Abilities that are loaded from the configured :ref:`packages <packages-label>`.
Each list entry is indexed by a number, so that you can refer to this Ability
by its associated number. For instance, to use the ``Ping a target`` Ability,
you would type ``list`` and then ``use 1`` to select the Ability for use,
because it is the first listed::

    pw> list
    1 Ping a target -- []
    2 Ping a prefix -- []
    3 DNSProxy -- ['Application_Layer', 'Threaded', 'DNS']
    pw> use 1
    pw (Ping a target)>

While ``list`` enumerates all loaded standalone Abilities, this might not be
convient if you loaded a very large package containing tons of abilities. You
may use the ``search`` command to find any Ability that would be listed by
``list``. Search results are indexed, just like listed Abilities are.

``search`` matches Ability names by default, using a case-insensitive
comparison::

    pw> search ping
    1 ping a target -- 
    2 ping a prefix -- 
    pw> search dns
    1 dnsProxy -- Application_Layer, Threaded, DNS

You can also search by tags::

    pw> search app
    No matching ability found.
    pw> search -a application_layer
    1 DNSProxy -- application_layer, Threaded, DNS

Searching by tags is eased by autocompletion that will provide you with a list
of all the tags that are registered by currently available Abilities.

Searches for tags may use multiple tags simultaneously. When multiple tags using a logical operation
between tags (and or or) may be specified with flags. The ``-o`` flag
indicates an OR, while ``-a`` indicates an AND.

For instance, you could search for all Abilities that are related to DNS and to MITM::
    
    pw> search -a dns mitm
    No matching ability found.

You may also want to list all Abilities that are either related to DNS or to HTTP:: 

    pw> search -o dns http
    1 DNSProxy -- application_layer, Threaded, DNS

Any of these flags can be used if you are filtering with only one tag.

.. note::
    A default index is built when the framework starts. You can quickly re-open you current in-development Ability across
    framework restart by recalling the last ``use`` command to access it directly.

.. note:

    If an ability appear in red in the list, it means that one or more prerequisites to
    run this Ability are missing. You may try to select that Ability in order to get
    a list of error messages telling what is missing, or run ``editor`` on it to
    quickly investigate the reason of the failure.

After selecting an index, if no errors are displayed, you now are interacting
with a CLI specific to the selected Ability. This CLI is described in details in the next chapter.

.. _shell-interface-lvl2-label:

Configuring, editing and running an Ability
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once more, the ``help`` command is available to list the commands that are
available with this new interactive CLI, and the ``help`` command may be used
to obtain further details about the listed commands.

You may also get more details about the selected Ability, with the ``info``
command::

    pw (DNSProxy)> info
    ------------------------------ [ DNSProxy ] -------------------------------
    type: Standalone
    description: Replacement for DNSProxy
    authors: Florian Maury
    tags: Application_Layer, Threaded, DNS
    reliability: Incomplete
    ---------------------------------------------------------------------------


Details about the role and the usage of the selected Ability may also be
obtained with the ``howto`` command::

    pw (DNSProxy)> howto
    This DNS proxy intercepts DNS requests at OSI layer 2. 
    ...
    the real DNS server is connected to a different card than the victim.

The ``options`` command (or its alias ``ls``) lists the Ability parameters that may be set before
running that Ability::
    
    pw (DNSProxy)> options
    ------------------------------- [ Options ] -------------------------------
    fake_zone = /bin/true
    policy_zone = /bin/true
    ip_src (Optional) = None
    ip_dst (Optional) = None
    port_dst (Optional) = 53
    interface = None
    outerface (Optional) = None
    quiet = True
    ---------------------------------------------------------------------------

Options may be set to user values or reset to their default values using the
``set`` and ``clear`` commands. For instance, let's set some option value::

    pw (DNSProxy)> set ip_dst=8.8.8.8
    pw (DNSProxy)> set interface=eth0
    pw (DNSProxy)> set ip_src=192.0.2.1
    pw (DNSProxy)> options
    ------------------------------- [ Options ] -------------------------------
    fake_zone = /bin/true
    policy_zone = /bin/true
    ip_src (Optional) = 192.0.2.1
    ip_dst (Optional) = 8.8.8.8
    port_dst (Optional) = 53
    interface = eth0
    outerface (Optional) = None
    quiet = True
    ---------------------------------------------------------------------------

.. note::

    Some input parameters (such as IpOpt) support value generators. You can get
    a list of them using the autocompletion when trying to set a new value
    (``set ip_dst=`` + ``Tab Tab``) to them.

    For instance, you may set an IP address to the special value ``RandIP4``. A
    new IP address will be generated each time the Abliity is run::
    
        pw (DNSProxy)> set ip_dst=RandIP4
        pw (DNSProxy)> options
        ------------------------------- [ Options ] -------------------------------
        fake_zone = /bin/true
        policy_zone = /bin/true
        ip_src (Optional) = 192.0.2.1
        ip_dst (Optional) = RandIP4
        port_dst (Optional) = 53
        interface = eth0
        outerface (Optional) = None
        quiet = True
        ---------------------------------------------------------------------------
        
    You may also use this special keyword as a function, to set a random value
    to the variable. This random value won't change across runs::

        pw (DNSProxy)> set ip_dst=RandIP4()
        pw (DNSProxy)> options
        ------------------------------- [ Options ] -------------------------------
        fake_zone = /bin/true
        policy_zone = /bin/true
        ip_src (Optional) = 192.0.2.1
        ip_dst (Optional) = 198.51.100.42
        port_dst (Optional) = 53
        interface = eth0
        outerface (Optional) = None
        quiet = True
        ---------------------------------------------------------------------------

.. note::

    If you try to set a invalid value for an option, you will receive an error
    message and the stored option value will remain unchanged. Each type of options
    is designed with a set of constraints, including some customizable ones, to
    validate the values that may be assigned to it.


Now let's reset the source IP address to its default value::

    pw (DNSProxy)> clear ip_src
    pw (DNSProxy)> options
    ------------------------------- [ Options ] -------------------------------
    fake_zone = /bin/true
    policy_zone = /bin/true
    ip_src (Optional) = None
    ip_dst (Optional) = 8.8.8.8
    port_dst (Optional) = 53
    interface = eth0
    outerface (Optional) = None
    quiet = True
    ---------------------------------------------------------------------------

Now let's reset all options to their default value::

    pw (DNSProxy)> clear
    pw (DNSProxy)> options
    ------------------------------- [ Options ] -------------------------------
    fake_zone = /bin/true
    policy_zone = /bin/true
    ip_src (Optional) = None
    ip_dst (Optional) = None
    port_dst (Optional) = 53
    interface = None
    outerface (Optional) = None
    quiet = True
    ---------------------------------------------------------------------------

Once you and your options are all set, you may run the Ability with the ``run``
command::

    pw (DNSProxy)> run

Abilities may run until they are done with their tasks. In that case,
they will give back control to the CLI once they terminated. Other Abilities
may start some services and are designed to run until interrupted by the SIGINT
signal (ctrl+c). Of course, you may interrupt any running Ability, in case it
went into an infinite loop of sorts, with the same key sequence.

If you are satisfied by the results of the Ability that you just run, you
may want to save the parameter values that you used. This enables you to reload
them, during a future session of PacketWeaver, or to back them up for a future
audit report, for instance.

To save the current parameter values, you may use the ``save`` command::

    pw (DNSProxy)> save /path/to/file.ini

To reload them, you may use the ``load`` command::

    pw (DNSProxy)> load /path/to/file.ini

At some point, you may feel the need to make some minor code adjustments in the
Ability you are about to run (e.g. a bug fix...). You don't need to exit
PacketWeaver for this.  The ``editor`` command will open the source code file
of the selected Ability and of all other Abilities that take part in the
selected Ability operations. Which source code editor is run is configured
within PacketWeaver :ref:`configuration <configuration-label>` file.

Finally, once configured you may ask of PacketWeaver to automatically generate
a shell command line that will run this Ability with the current configuration
from shell::

    pw (DNSProxy)> cmd
    export PW_OPT_FAKE_ZONE='/bin/true'
    export PW_OPT_POLICY_ZONE='/bin/true'
    export PW_OPT_IP_SRC='None'
    export PW_OPT_IP_DST='None'
    export PW_OPT_PORT_DST='53'
    export PW_OPT_INTERFACE='None'
    export PW_OPT_OUTERFACE='None'
    export PW_OPT_QUIET='True'
    export PYTHONPATH='/opt/pw/pw/packetweaver:/usr/local/lib/python2.7/dist-packages/python_twitter-1.0-py2.7.egg:/usr/local/lib/python2.7/dist-packages/oauth2-1.5.211-py2.7.egg:/usr/local/lib/python2.7/dist-packages/pympress-0.3-py2.7.egg:/opt/pw/pw:/usr/lib/python2.7:/usr/lib/python2.7/plat-x86_64-linux-gnu:/usr/lib/python2.7/lib-tk:/usr/lib/python2.7/lib-old:/usr/lib/python2.7/lib-dynload:/usr/local/lib/python2.7/dist-packages:/usr/lib/python2.7/dist-packages:/usr/lib/python2.7/dist-packages/PILcompat:/usr/lib/python2.7/dist-packages/gst-0.10:/usr/lib/python2.7/dist-packages/gtk-2.0:/usr/lib/python2.7/dist-packages/ubuntu-sso-client:/usr/lib/python2.7/dist-packages/ubuntuone-client:/usr/lib/python2.7/dist-packages/ubuntuone-couch:/usr/lib/python2.7/dist-packages/ubuntuone-storage-protocol:/opt/pw/scapy'
    python /opt/pw/pw/packetweaver/pw.py use -p base -a DNSProxy --fake_zone=${PW_OPT_FAKE_ZONE} --policy_zone=${PW_OPT_POLICY_ZONE} --ip_src=${PW_OPT_IP_SRC} --ip_dst=${PW_OPT_IP_DST} --port_dst=${PW_OPT_PORT_DST} --interface=${PW_OPT_INTERFACE} --outerface=${PW_OPT_OUTERFACE} --quiet=${PW_OPT_QUIET}

This command line can be copy/pasted in a shell console to start the ability with these options.

.. warning:: This command line generation is experimental and might quickly evolve.

.. note:: You can also use the ``cmd oneline`` option to get a bash oneline command that can be directly tested.
