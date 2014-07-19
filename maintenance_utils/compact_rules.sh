# Run this in a sibling to a checkout of the rosdistro repository to
# load all rules files and write back in compact canonical form.
find ../rosdistro/rosdep -name *.yaml -exec xylem _compact_rules_file {} -w \;
