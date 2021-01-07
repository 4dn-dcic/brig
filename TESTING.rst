=======================
Testing a brig function
=======================

This document describes various ways to test this repository.


Set Up a Virtual Environment
============================

**Before testing** make sure you have built a virtual environment in the toplevel directory of the ``brig`` repository,
and make sure you've selected that environment. For example::

   $ python3 -m venv benv

or if using ``pyenv``::

   $ pyenv exec python -m venv benv


Populate the Virtual Environment
================================

Populate the virtual environment. Some tools like PyCharm will want this.
Note that this virtual environment is used *only* for debugging and testing::

  $ poetry install


Execute Commands in This Function's Folder
==========================================

Select this subfolder of the ``brig`` repository::

   $ cd functions/<function-name>

If the function is part of an API, that will be::

   $ cd apis/<api-name>/functions/<function-name>


Running The Tests
=================

From within the function folder, use ``brig-test`` to do testing::

   $ brig-test

This command will freshly build requirements from ``requirements.txt``
in the current folder, placing them along with source file (from the ``src/``
subfolder) and putting them in the ``stg/`` subfolder. These will be run there.

The build will also be zipped into ``bld/`` and a link will be created
from ``bld/staged`` to the zip being tested. Note that this works
by calling::

   $ brig-build --test-only

Note that ``brig-build`` always runs tests first, but if given this
``--test-only`` argument, it will stop wiht that.  If the argument is omitted,
thne if testing succeeds, ``brig-build`` will also link``bld/current`` to
the zip that was created. If the test fails, or if ``--test-only`` is given,
then that link won't be created. (Also, if ``bld/current`` *is* updated,
the previous target of ``bld/current`` will be available through the link
``bld/previous``.
