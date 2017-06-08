Developing Abilities
====================

This section describes the writing of an Ability. 

First, we will take a look at the boilerplate, which is common to all
Abilities. 

Then, we will look at the way to insert your code into this boilerplate, and
how to take advantage of the predefined builtin parameter types.

We will also cover how to handle external library imports with regards to
PacketWeaver built-in mechanism to detect missing requirements.

Then, we will cover the topic of nested Abilities, and how to send parameters
and get results from an Ability.

Finally, we will study how to start parallel Abilities, how they communicate,
and how to interact with them.

.. toctree::
   :maxdepth: 2

   dev/abl_writing_base
   dev/abl_writing_advanced
   dev/abl_thread_orchestration
