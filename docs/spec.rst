.. _rules-files:

=================
xylem Rules files
=================

.. automodule:: xylem.specs.rules

Notes
~~~~~

- Rules files compacted with this syntax can be found here:
  https://github.com/NikolausDemmel/rosdistro/tree/xylem/rosdep
- With the proposed rules files the following entries are not valid any
  more. ``homebrew`` is interpreted as a version of osx and ``packages``
  as the package-manager. No detection of this problem happens at the
  moment:

  .. code-block:: yaml

      boost:
        osx:
          homebrew:
            packages: [boost]

  Correct would be:

  .. code-block:: yaml

      boost:
        osx:
          any_version:
            homebrew:
              packages: [boost]

- ``'any_version'`` is somewhat limited in some cases:

  .. code-block:: yaml

      gazebo:
        ubuntu:
          precise: [gazebo]
          quantal: [gazebo]
          raring: [gazebo]
          saucy: [gazebo2]
          trusty: [gazebo2]

  Using ``any_version`` for ``saucy`` and ``trusty`` does not contain
  information from which version the rule has been tested/confirmed. In
  this case it would also apply to ``precise``, whereas the explicit
  list above would give a more meaningful error on precise ("No rules
  definition" instead of "Failed to install apt package gazebo2").

- Here is another limitation, where rules for all versions but the
  latest are the same:

  .. code-block:: yaml

      ffmpeg:
        ubuntu:
          lucid: [ffmpeg, libavcodec-dev, libavformat-dev, libavutil-dev, libswscale-dev]
          maverick: [ffmpeg, libavcodec-dev, libavformat-dev, libavutil-dev, libswscale-dev]
          natty: [ffmpeg, libavcodec-dev, libavformat-dev, libavutil-dev, libswscale-dev]
          oneiric: [ffmpeg, libavcodec-dev, libavformat-dev, libavutil-dev, libswscale-dev]
          precise: [ffmpeg, libavcodec-dev, libavformat-dev, libavutil-dev, libswscale-dev]
          quantal: [ffmpeg, libavcodec-dev, libavformat-dev, libavutil-dev, libswscale-dev]
          raring: [ffmpeg, libavcodec-dev, libavformat-dev, libavutil-dev, libswscale-dev]
          saucy: [ffmpeg, libavcodec-dev, libavformat-dev, libavutil-dev, libswscale-dev]
          trusty: [libavcodec-dev, libavformat-dev, libavutil-dev, libswscale-dev]

  We might want to allow tuple/list/set as version dict key or maybe
  range of versions ``'lucid - saucy'`` to alleviate that problem.
- For implementing verions ranges part of the problem is that versions
  are not known and cannot be listed, only detected. Can we change that
  easily? OS plugins could list all known versions, but that would
  require adding any new version explicitly. Maybe not so bad?
- Should special keys have special syntax like ``*any_os*`` or similar?
  + *Nikolaus*: IMHO no


.. _verions-ranges-and-geq:

any_version and version ranges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The above notes mention some problems with the initial proposal for
``any_version``.

Firstly, ``any_version`` applies to all version, even old ones for which
it the rule has not been tested. ``any_version`` is often used to make
sure the rule applies to any newly released versions and therefore used
instead of a definition for the currently latest version. This makes
sure that when a new OS version is released, only the keys for which the
rule actually has to change need to be touched in the rules file. At the
moment it is not possible to express a minimal version for which the
``any_version`` rule is valid. Therefore, replacing a list of explicit
definitions for each version with a ``any_version`` rule actually loses
information.

Secondly, in the above example of ``ffmpeg``, only the latest version
has changed. Since we want to use ``any_version`` for the latest
version, we have to retain the repeated explicit definition for all
other versions (which are identical).

any_version with greater or equal condition
-------------------------------------------

We propose the following two changes to alleviate those problems. Firstly,
installer dicts underneath ``any_version`` may optionally have a key
``any_version_geq`` mapping to a minimal version to which the rule
applies, for example:

.. code-block:: yaml

  gazebo:
    ubuntu:
      precise: [gazebo]
      quantal: [gazebo]
      raring: [gazebo]
      any_version:
        any_version_geq: saucy
        packages: [gazebo2]

There exist short notations.

.. code-block:: yaml

  gazebo:
    ubuntu:
      precise: [gazebo]
      quantal: [gazebo]
      raring: [gazebo]
      any_version>=saucy: [gazebo2]

The above expands to the initial example.

.. code-block:: yaml

  gazebo:
    ubuntu>=saucy: [gazebo2]

The above exands to the initial example without the rules for precise,
raring and quantal.

This means that for rule lookup the order on versions needs to be known.
Therefore, each os plugin needs to provide an order over its version
strings. Note that the order is not needed for rules file expansion.


Multiple versions in one defintion
----------------------------------

We allow to define multiple versions in one definition by allowing the
keys in the version dict to be a comma separated list of versions (as a
string). Upon rule expansion the definitions are separated as one
definition for each listed version. We do *not* provide a way to specify
version ranges (like ``precise - saucy``) to keep the implied versions
explicit. This also helps to not require the list of all versions for
rule expansion.

For example, the above ``ffmpeg`` definition can be compacted as:

.. code-block:: yaml

  ffmpeg:
    ubuntu:
      lucid, maverick, natty, oneiric, precise, quantal, raring, saucy: [ffmpeg, libavcodec-dev, libavformat-dev, libavutil-dev, libswscale-dev]
      any_version>=trusty: [libavcodec-dev, libavformat-dev, libavutil-dev, libswscale-dev]

