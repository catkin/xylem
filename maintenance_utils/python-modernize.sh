#!/usr/bin/env bash
# Install development version from this fork:
# https://github.com/takluyver/python-modernize
# Seems to be more maintained
# Run in root of xylem repository to update python files in such a way
# as to make maintaining portable py2/py3 code easier.
python-modernize xylem test --future-unicode
