.. _rules-files:

=================
xylem Rules files
=================

.. automodule:: xylem.specs.rules

**Notes**

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

- Also, ``'any_version'`` for the latest version does not contain
  information up to which version the rule has been tested/confirmed.
- Allow tuple/list/set as version dict key or maybe range of versions
  ``'lucid - oneric'``?
- For the above part of the problem is that versions are not known and
  cannot be listed, only detected. Can we change that easily? OS plugins
  could list all known versions, but that would require adding any new
  version explicitly. Maybe not so bad?
- Should special keys have special syntax like ``*any_os*`` or similar?
  + *Nikolaus*: IMHO no
