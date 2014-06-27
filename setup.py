#!/usr/bin/env python

from setuptools import setup, find_packages

# see: http://reinout.vanrees.org/weblog/2009/12/17/managing-dependencies.html
tests_require = ['nose', 'flake8', 'mock', 'coverage']

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
        'License :: OSI Approved :: BSD License',
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
        'Topic :: System :: Installation/Setup'
    ],
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
            'update = xylem.commands.update:definition',
            'resolve = xylem.commands.resolve:definition'
        ],
        'xylem.specs': [
            'rules = xylem.specs.rules:definition'
        ],
        'xylem.os': [
            'debian = xylem.os_support.plugins:Debian',
            'ubuntu = xylem.os_support.plugins:Ubuntu',
            'osx    = xylem.os_support.plugins:OSX'
        ],
        'xylem.installers': [
            'fake = xylem.installers.fake:definition'
        ]
    }
)
