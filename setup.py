#!/usr/bin/env python

from setuptools import setup, find_packages

# TODO: read README and LICENSE files to compose "long description"
#
# This might be useful:
# http://stackoverflow.com/questions/1192632/how-to-convert-restructuredtext-to-plain-text
# http://www.jeffknupp.com/blog/2013/08/16/open-sourcing-a-python-project-the-right-way/

# see: http://reinout.vanrees.org/weblog/2009/12/17/managing-dependencies.html
tests_require = ['nose', 'flake8', 'mock', 'coverage', 'testfixtures']

setup(
    name='xylem',
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    package_data={
        'xylem.sources': [
            'xylem/sources/sources.d/*'
        ]
    },
    include_package_data=True,
    install_requires=[
        'six',
        'PyYAML',
        'argparse',
    ],
    tests_require=tests_require,
    extras_require={'test': tests_require},
    author='Nikolaus Demmel',
    author_email='nikolaus@nikolaus-demmel.de',
    maintainer='Nikolaus Demmel',
    maintainer_email='nikolaus@nikolaus-demmel.de',
    url='https://github.com/catkin/xylem',
    keywords=['caktin', 'bloom', 'package manager'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha'
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development',
        'Topic :: System :: Installation/Setup',
    ],
    description="xylem is a package manager abstraction tool.",
    long_description="xylem is a package manager abstraction tool.",
    license='Apache License 2.0',
    test_suite='test',
    entry_points={
        'console_scripts': [
            'xylem = xylem.commands.main:main',
            'xylem-update = xylem.commands.update:main',
        ],
        'xylem.commands': [
            'update = xylem.commands.update:definition',
            'resolve = xylem.commands.resolve:definition',
            'lookup = xylem.commands.lookup:definition',
            '_compact_rules_file = xylem.commands._compact_rules_file:definition',
        ],
        'xylem.specs': [
            'rules = xylem.specs.plugins.rules:definition',
        ],
        'xylem.os': [
            'debian = xylem.os_support.plugins:debian_definition',
            'ubuntu = xylem.os_support.plugins:ubuntu_definition',
            'xubuntu = xylem.os_support.plugins:xubuntu_definition',
            'osx    = xylem.os_support.plugins:osx_definition',
        ],
        'xylem.installers': [
            'fake = xylem.installers.plugins.fake:definition',
            'apt = xylem.installers.plugins.apt:definition',
            'homebrew = xylem.installers.plugins.homebrew:definition',
            'macports = xylem.installers.plugins.macports:definition',
            'pip = xylem.installers.plugins.pip:definition',
        ],
    }
)
