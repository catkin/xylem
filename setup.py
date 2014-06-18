#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='xylem',
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    package_data={
        'xylem.sources': [
            'xylem/sources/sources.list.d/*'
        ]
    },
    include_package_data=True,
    install_requires=[
        'six',
        'PyYAML',
        'argparse',
    ],
    author='William Woodall',
    author_email='william@osrfoundation.org',
    maintainer='William Woodall',
    maintainer_email='william@osrfoundation.org',
    url='http://www.ros.org/wiki/xylem',
    keywords=['caktin', 'bloom', 'package manager'],
    classifiers=['Programming Language :: Python',
                 'License :: OSI Approved :: BSD License'],
    description="xylem is a package manager abstraction tool.",
    long_description="xylem is a package manager abstraction tool.",
    license='BSD',
    test_suite='test',
    entry_points={
        'console_scripts': [
            'xylem = xylem.commands.main:main',
            'xylem-update = xylem.commands.update:main'
        ],
        'xylem.commands': [
            'update = xylem.commands.update:description'
        ],
        'xylem.specs': [
            'rules = xylem.specs.rules:rules_spec_parser'
        ],
        'xylem.os': [
            'debian = xylem.os_support.plugins:Debian',
            'ubuntu = xylem.os_support.plugins:Ubuntu',
            'osx    = xylem.os_support.plugins:OSX'
        ],
        'xylem.installers': [
            'fake = xylem.installers.fake:description'
        ]
    }
)

# TEST requires: mock
