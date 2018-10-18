.. _installation-label:

Installation
------------
All you need to do is getting the source code using git.

.. note:: The framework was tested under Ubuntu 18.04 LTS (amd64).

There are no distribution/pip packages of this framework available yet,
but this definitely is on our todo-list.

Sources and dependencies
^^^^^^^^^^^^^^^^^^^^^^^^
Browse to your favorite git cloning destination folder (e.g. ~/git/) and clone the PacketWeaver directory::

    git clone https://github.com/ANSSI-FR/packetweaver
    cd packetweaver

Packetweaver has no strong external dependencies. This means you should be
ready to go, if you have just the Python3 interpreter and the Python standard
library. If you ever ran Packetweaver that way, however, you would miss quite a
bunch of helpers that would be automatically disabled.

To enable these helpers, you might want to install some or all of the following
dependencies:

* pyroute2
* gmpy2
* pcapy

The easiest way to install them is to use a combination of your package manager and pip3::

    sudo apt install python3 python3-dev build-essential libpcap-dev python3-pip libgmp-dev libmpfr-dev libmpc-dev
    sudo pip3 install pyroute2 gmpy pcapy pyroute2

:ref:`Packages <packages-label>` might require additional dependencies. Please refer to their documentation.

.. seealso:: More dependencies are required if you wish to build this :ref:`documentation <build-doc-label>` offline or run the framework automated :ref:`tests<run-tests-label>`.

Run it
^^^^^^

Once PacketWeaver retrieved from git, you may run it from shell using the ``run_pw`` script::

    ./run_pw

You might need to make some minor adjustments to the configuration file::

    vim packetweaver/pw.ini

.. seealso:: :ref:`Configuration file documentation section <configuration-label>`

If PacketWeaver displayed its banner and the ``pw>`` prompt, you are now good to go.

You can now hit "ctrl+d" or type in the ``exit`` command to quit PacketWeaver and start browsing the next section of this documentation!


