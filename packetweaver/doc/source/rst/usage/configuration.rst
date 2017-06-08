.. _configuration-label:

Configuration
=============

PacketWeaver can be configured with an .ini file. The default config file is
located in PacketWeaver installation directory. This is the one used when 
running the ``run_pw`` shell script. However, you may specify another location
using the command line option ``--config`` or ``-c`` for short. In that case,
the syntax is::

    $ ./run_pw --config=/path/to/my/pw.ini interactive


The configuration file is composed of four sections:
* Dependencies
* Packages
* Tools
* Internals

Each of these sections are described herebelow.

.. note:: Make sure to restart the framework after a modification to take the new parameters into account.

Dependencies Configuration Section
----------------------------------

The Dependencies section contains a list of Python module paths that will be
added to your PYTHONPATH environment variable during PacketWeaver execution.
Its only purpose is to spare you from setting the PYTHONPATH environment
variable before each run of PacketWeaver. For this reason, the section only
need to contain path of dependencies that are not already in the Python default
import paths and in the PYTHONPATH environment variable that you may have set
otherwise.

Key names does not matter in this section and only need to be unique.

For example, if you want to use the lastest `Scapy <https://github.com/secdev/scapy>`_ 
version, you may clone it whatever git directory you use (e.g. ~/git) and set
your ``Dependencies`` section as follows::

    [Dependencies]
    scapy=/absolute/path/to/scapy/

If you want to use a relative a path, the path must be relative to the
directory of your *packetweaver/pw.py* file. If Scapy repository was cloned in
the same directory as your PacketWeaver repository, you would set your
configuration like this::

    [Dependencies]
    scapy=../../scapy/

Finally several paths can be specified, using two different keys::

    [Dependencies]
    scapy=../../scapy/
    yourlib=../../yourlib/


.. _configuration-package-label:

Packages Configuration Section
------------------------------

PacketWeaver enables you to file your Abilities into seperate logical groups of
Abilities. These groups of Abilities are called Packages in the PacketWeaver
lingo. You may want to organize your Abilities like this because they all share
a common set of dependencies. Or maybe there are all interdependent. Or maybe
they share a common goal or purpose. Or maybe you are the type to label
everything. No judge.

Packetweaver loads at startup all packages that are declared in this
configuration section. The more packages you have, the more results are
displayed by the ``list`` interactive command line command and the more
Abilities can be found with the ``search`` command. The more packages are
loaded, the slower Packetweaver is to startup.

.. note:: 

    In the Packages configuration section, key names are crucial, and
    renaming them might be expensive. Indeed, there might be some source code
    references to that name, when declaring interdependencies between Abilities.
    Thus, it is advised to use virtually unique package names. For instance one
    could use a prefix to namespace the package names:
    ``mycompanyname_dancing_monkey``. 

The entry values of this section are paths to Python modules that are valid
PacketWeaver packages. Please, refer to the :ref:`Writing a package <packages-label>`
section of this documentation for more information about Packages declaration.
Paths may be absolute paths on the filesystem, or paths relative to the
``pw.py`` file, just like for the Dependencies configuration section.

For example, your Packages configuration section might look like this::

    [Packages]
    base=abilities/
    mycompany_flying_monkeys=/opt/pw_circus/
    mycompany_ducking_ducks=../../pkgs/missing_animals/abilities/

Tools Configuration Section
---------------------------
This section only contains one configuration key hitherto: ``editor``.

Editor
^^^^^^

The Editor option lets you select your favorite text editor. It will be used by
the ``editor`` command available in the interactive CLI, after you selected an
Ability. For instance, you would configure this option to be:

* your default system editor (probably graphical)::

    [Tools]
    editor=xdg-open

* a text mode editor::

    [Tools]
    editor=vim

* a text mode editor using options::

    [Tools]
    editor=emacs -nw


Internals configuration section
-------------------------------
This section only contains one configuration key hitherto: HistFile.

History
^^^^^^^

The PacketWeaver interactive CLI offers command history. This history is saved
to a dedicated file. You can customize its name and location by editing the
``HistFile`` configuration key. To store it in your home directory, you may
specify::

    [Internals]
    HistFile=~/.pwhistory

Paths are expanded if need be.
