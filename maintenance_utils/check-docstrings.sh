#!/usr/bin/env sh
# Run this in the root of the xylem repository to check docstrings with the
# pep257 tool. Some specific warnings that are silenced because they are
# deliberate wontfixes. Missing docstring warnings are also silenced.
pep257 xylem --ignore D100,D101,D102,D103 2>&1 |
    grep -v "xylem/.*/__init__.py WARNING: __all__" |
    pcregrep -v -M 'xylem/update.py:\d+ in public function `load_url`:\n *D((301)|(207))'
