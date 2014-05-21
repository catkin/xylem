``xylem``
=================

``xylem`` is a package manager abstraction tool.
It can be used to install dependencies on any supported platform.

For example, if you want to install ``boost`` on your machine you would
simply run ``xylem install boost``. This command would cause ``xylem``
to determine your OS and OS Version, look up the corresponding package
managers for that OS, OS Version tuple, look up the appropriate value
for ``boost`` for that OS pair, and finally invoke the package manager
to install boost, e.g. for Ubuntu that might be ``sudo apt-get install
libboost-all-dev``.

This tool allows you to generalize your installation instructions and
define your software package's dependencies once. ``xylem`` also has an
API which can be used to automate installation of resources, like for
automated tests or for simplified installation scripts.

Contents:

.. toctree::
   :maxdepth: 2

   design
   spec
   xylem_api
   apidoc/xylem

Installing from Source
----------------------

Given that you have a copy of the source code, you can install ``xylem``
like this:

.. code-block:: bash

    $ python setup.py install

.. note::

    If you are installing to a system Python you may need to use
    ``sudo``.

If you do not want to install ``xylem`` into your system Python, or you
don't have access to ``sudo``, then you can use a `virtualenv
<https://virtualenv.pypa.io/>`_.

Hacking
-------

Because ``xylem`` uses `setuptools
<http://pythonhosted.org/setuptools/>`_ you can (and should) use the
`develop <http://pythonhosted.org/setuptools/setuptools.html
#development-mode>`_ feature:

.. code-block:: bash

    $ python setup.py develop

.. note::

    If you are developing against the system Python, you may need
    ``sudo``.

This will "install" ``xylem`` to your Python path, but rather than
copying the source files, it will instead place a marker file in the
``PYTHONPATH`` redirecting Python to your source directory. This allows
you to use it as if it were installed but where changes to the source
code take immediate affect.

When you are done with develop mode you can (and should) undo it like
this:

.. code-block:: bash

    $ python setup.py develop -u

.. note::

    If you are developing against the system Python, you may need
    ``sudo``.

That will "uninstall" the hooks into the ``PYTHONPATH`` which point to
your source directory, but you should be wary that sometimes console
scripts do not get removed from the bin folder.


Code Style
----------

The source code of ``xylem`` aims to follow the Python `style guide
<http://docs.python-guide.org/en/latest/writing/style>`_ and the
:pep:`8` guidelines. In particular a line width of 79 characters is
enforced for python code, while multiline comments or docstrings as well
as text files should use a line width of 72.

The test-suite checks that all xylem code passes the ``flake8``. On top
of that identifer names should follow the rules layed out in :pep:`8
#naming-conventions` and docstrings should adhere to :pep:`257`, however
these are not automatically checked.

The most important rules are readability and consistency and use of
common sense.

Testing
-------

In order to run the tests you will need to install `nosetests
<https://nose.readthedocs.org/>`_ and `flake8
<https://flake8.readthedocs.org/>`_.

Once you have installed those, then run ``nosetest`` in the root of the
``xylem`` source directory:

.. code-block:: bash

    $ nosetests

Building the Documentation
--------------------------

In order to build the docs you will need to first install `Sphinx <http
://sphinx-doc.org/>`_.

You can build the documentation by invoking the Sphinx provided make
target in the ``docs`` folder:

.. code-block:: bash

    $ # In the docs folder
    $ make html
    $ open _build/html/index.html

Sometimes Sphinx does not pickup on changes to modules in packages which
utilize the ``__all__`` mechanism, so on repeat builds you may need to
clean the docs first:

.. code-block:: bash

    $ # In the docs folder
    $ make clean
    $ make html
    $ open _build/html/index.html
