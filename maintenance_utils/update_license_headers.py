#!/usr/bin/env python

# Run in root of xylem directory to add / update the license header in
# all python files

# TODO: support updating the header but retaining the year, possibly based on file edit date-time

import argparse
import os
import re
import fnmatch


def read_file(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    return data.decode('utf-8')


def write_file(filename, content):
    data = content.encode("utf-8")
    with open(filename, 'wb') as f:
        f.write(data)


def process_args(args):

    args.license_header = read_file(args.license_header)

    args.old_header = re.compile("|".join(map(read_file, args.old_header) + [re.escape(args.license_header)]), re.MULTILINE)
    args.except_dirs = re.compile("|".join(map(fnmatch.translate, args.except_dirs)))
    args.matching = re.compile("|".join(map(fnmatch.translate, args.matching)))
    args.except_matching = re.compile("|".join(map(fnmatch.translate, args.except_matching)))
    args.except_content = re.compile("|".join(args.except_content), re.MULTILINE)


def replace_headers(args):
    count = 0
    for path in args.path:
        count += replace_headers_recursive(path, args)
    return count


def replace_headers_recursive(path, args):
    count = 0
    if os.path.islink(path):
        if args.verbose:
            print("%s -- ignoring symbolic link" % path)
    elif os.path.isfile(path):
        filename = os.path.basename(path)
        if args.matching.match(filename):
            if not args.except_matching.match(filename):
                count += replace_headers_file(path, args)
            else:
                if args.verbose:
                    print("%s -- ignoring excluded filename" % path)
        else:
            if args.verbose:
                print("%s -- ignoring not included filename" % path)
    elif os.path.isdir(path):
        if args.except_dirs.match(path):
            if args.verbose:
                print("%s -- ignoring excluded directory" % path)
        else:
            if args.verbose:
                print("%s -- descending into directory" % path)
            for p in os.listdir(path):
                count += replace_headers_recursive(os.path.join(path, p), args)
    else:
        if args.verbose:
            print("%s -- ignoring unknown directory entry" % path)
    return count


def replace_headers_file(path, args):
    count = 0
    content = read_file(path)
    if args.except_content.search(content):
        if args.verbose:
            print("%s -- ignoring file excluded content" % path)
    else:
        match = args.old_header.search(content)
        if match:
            if content[match.start():match.end()] == args.license_header:
                print("%s -- up to date" % path)
            else:
                print("%s -- replacing old header" % path)
                content = content[:match.start()] + args.license_header + content[match.end():]
                count += 1
                if args.write:
                    write_file(path, content)
        else:
            lines = content.splitlines(True)
            if lines[0].startswith("#!"):
                print("%s -- inserting new header after shebang" % path)
                insert_header(lines, 1, args.license_header)
            elif lines[0].startswith("# -*-"):
                print("%s -- inserting new header after special first comment line" % path)
                insert_header(lines, 1, args.license_header)
            else:
                print("%s -- inserting new header at the beginning of file" % path)
                insert_header(lines, 0, args.license_header)
            count += 1
            if args.write:
                write_file(path, "".join(lines))
    return count


def insert_header(lines, index, header):
    if len(lines) > index:
        if not lines[index].isspace():
            lines.insert(index, "\n")
    lines.insert(index, header)
    if index > 0:
        if not lines[index-1].isspace():
            lines.insert(index, "\n")


def main():

    parser = argparse.ArgumentParser(
        description="Update the license header in source files.")

    add = parser.add_argument

    add("path", nargs="+",
        help="Paths to search for source files in.")
    add("--license-header", "-l", required=True,
        help="License header file. The exact content of this file will be \
inserted as a license header (if not present already).")
    add("--old-header", "-o", action="append",
        help="File containing a multiline python regular expression to \
look for existing license headers in source files. May be passed multiple \
times. If any of the regular expressions match, the matched text is replaced \
with the new header.")
    add("--except-dirs", action="append",
        help="Glob pattern matching directories which to ignore. May be \
passed multiple times.")
    add("--matching", action="append",
        help="Glob pattern matching files for which to replace headers. \
May be passed multiple times.")
    add("--except-matching", action="append",
        help="Glob pattern matching files which to ignore. Takes precedence \
over '--matching'. May be passed multiple times.")
    add("--except-content", action="append",
        help="Multiline regular expression matching file content. If it \
matches, file is ignored. May be passed multiple times.")
    add("--write", "-w", action="store_true",
        help="If not passed, no files are actually modified.")
    add("--verbose", "-v", action="store_true",
        help="If passed, verbose output on ignored files and folders.")

    args = parser.parse_args()

    if not args.matching:
        matching = ["*"]

    if args.verbose:
        print("Arguments:")
        print(args)

    process_args(args)

    count = replace_headers(args)

    if count == 0:
        print("Did not need to update any files.")
    else:
        if args.write:
            print("Updated %s files." % count)
        else:
            print("Would have updated %s files. Run again with `-w` to "
                  "actually update the files." % count)


if __name__ == "__main__":
    main()
