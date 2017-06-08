.. _run-tests-label:

Non-regression tests
====================

The test coverage of the framework is one of the main current task. We use the `Pytest <https://docs.pytest.org/en/latest/>`_
library to perform standard unit tests on the framework core, and `Mypy
<http://mypy-lang.org/>`_ setup is on the way to perform static typing analysis.

All the tests may be run with the *packetweaver/run_pw_tests* script.

Installing the testing toolset
------------------------------

As mentioned above, you only need to install pytest, with an extension used to
perform test code coverage analysis::

    pip install pytest pytest-cov

Unit tests
----------

These are the classic unit tests that help enforce the correct internal functioning of the framework.

The main script encapsulates two pytest functionalities: one to run a coverage test and another to start a python debugger
in case of a test failure. The corresponding commands may be used like this::

    ./run_pw_tests utest        # run all the pytest tests
    ./run_pw_tests utest --cov  # run a code covering test and display its report
    ./run_pw_tests utest --pdb  # run a debugger in case of test failure
    ./run_pw_tests utest --cov --pdb
