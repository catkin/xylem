#!/usr/bin/env sh
# Run this in the doc directory of the xylem repository. It uses sphinx-apidoc
# to create documentation files for the xylem packages. Any arguments are passed
# to sphinx-apidoc, so e.g. use
#     ./create-apidoc.sh -f
# to overwrite existing files.
sphinx-apidoc -o apidoc ../xylem $@
