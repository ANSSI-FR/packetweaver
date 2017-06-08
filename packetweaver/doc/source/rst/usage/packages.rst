.. _packages-label:

Packages
========

Functionally speaking, a PacketWeaver package is a set of Abilities, grouped by
purpose, topic, authors, interdependencies, version control access-control or
whatever other reasons you might think of. Having this package feature enables
you to share/publish only parts of your scripts. It also introduces namespaces,
because Abilities must have a unique name within a same package, but a same
name can be reused across packages.

Python-wise, a PacketWeaver package is a Python module, whose ``__init__.py``
file contains a global variable called ``exported_abilities``. This variable
contains a list of class objects inheriting (directly or indirectly) from the
``AbilityBase`` class.

Basic structure
^^^^^^^^^^^^^^^

We suggest that you structure your PacketWeaver packages as follows::

    pw-pkg-test/
    ├── doc/
    └── abilities/
        ├── demo/
        │   ├── demo_app.py
        │   └── __init__.py
        ├── __init__.py
        └── test_app.py

The ``abilities`` folder is a Python module, whose ``__init__.py`` contains a
list of the activated abilities::

    import test_app
    from demo import demo_app

    exported_abilities = [
        test_app.Ability,
        demo_app.Ability,
    ]

In that case, ``test_app.py`` and ``demo_app.py`` both contain a Python class
called ``Ability`` that herites from ``AbilityBase``. Abilities must be
declared in this list to be usable by other Abilities or to be listed by the
PacketWeaver CLI.

.. _activate-pkg-label:

Package usage
^^^^^^^^^^^^^

To use a package, you must declare it in PacketWeaver configuration file, as
described in the :ref:`configuration <configuration-package-label>` file
section.


Naming convention
^^^^^^^^^^^^^^^^^

Most Abilities are stored in separate Python files, each containing an Ability
called ``Ability``.

PacketWeaver package directories are generally named pw-pkg-<your_pkg_name>.
People will most probably import your package by configuring whatever you
defined as ``your_pkg_name`` as this package key for the PacketWeaver
configuration file Package section.  Since PacketWeaver package names must be
unique in a configuration file, it is advised that you prefix your package
name, for instance with the name of your company or group.
