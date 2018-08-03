.. _run-tests-label:

Testing
=======

Debug the framework
-------------------

Many logs are available in the PacketWeaver source code. If you need to
get more insight on the internal functioning, you can lower down the
logging framework logging level by running it with the following command::

    ./run_pw --log DEBUG interactive

The default logging levels are listed when issuing a simple::

    ./run_pw -h

Non-regression tests
--------------------

Unit tests are developed using the `Pytest <https://docs.pytest.org/en/latest/>` library,
and managed using the `Tox <https://tox.readthedocs.io/en/latest/>` utility.

When running the tests, Tox will automatically create and install in a virtualenv the required libraries, such as Pytest
for example. This means Tox is the only dependence required::

    python3 -m pip install tox


Running the most complete test procedure is done by running the `tox` command in same folder as the `tox.ini` file.
It will execute all the available unit tests, generated a coverage report and check the code for pep8 conformance.

To avoid running all of them, several environments have been defined. They can be run independently, using
the following commands::

    tox -e flake8
    tox -e …
