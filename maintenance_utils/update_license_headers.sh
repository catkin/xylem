#!/usr/bin/env bash

# Run in root of xylem repository

# When result looks ok, run again with `-w` to actually update the files

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
python "$DIR/update_license_headers.py" \
    xylem test \
    --license-header "$DIR/licenseheader.txt" \
    --old-header "$DIR/old_apache_licenseheader.regex" \
    --old-header "$DIR/old_bsd_licenseheader.regex" \
    --except-dirs ".*" \
    --matching "*.py" \
    --except-matching "setup.py" \
    --except-content "\A\Z" \
    $@
