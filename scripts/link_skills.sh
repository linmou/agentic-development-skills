#!/bin/sh
# Link direct repository skills into a configurable Codex runtime directory.

set -eu

usage() {
    echo "usage: $0 DESTINATION [SOURCE_ROOT]" >&2
    exit 2
}

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    usage
fi

destination=$1
source_root=${2:-$(CDPATH= cd -- "$(dirname "$0")/.." && pwd -P)}

if [ ! -d "$source_root" ]; then
    echo "source root is not a directory: $source_root" >&2
    exit 1
fi

skills_root=$source_root/skills
if [ ! -d "$skills_root" ]; then
    echo "skills directory is not a directory: $skills_root" >&2
    exit 1
fi

source_abs=$(CDPATH= cd -- "$source_root" && pwd -P)
if [ -e "$destination" ]; then
    destination_abs=$(CDPATH= cd -- "$destination" && pwd -P)
else
    destination_parent=$(dirname "$destination")
    destination_name=$(basename "$destination")
    destination_abs=$(CDPATH= cd -- "$destination_parent" && pwd -P)/$destination_name
fi

destination_suffix=${destination_abs#"$source_abs"/}
if [ "$destination_abs" = "$source_abs" ] || [ "$destination_suffix" != "$destination_abs" ]; then
    echo "source/destination collision: $destination" >&2
    exit 1
fi

if [ -L "$destination" ] || { [ -e "$destination" ] && [ ! -d "$destination" ]; }; then
    echo "destination is not a directory: $destination" >&2
    exit 1
fi

mkdir -p "$destination"

for skill_dir in "$skills_root"/*; do
    [ -d "$skill_dir" ] || continue
    [ -f "$skill_dir/SKILL.md" ] || continue
    name=$(basename "$skill_dir")
    link_path=$destination/$name
    if [ -L "$link_path" ]; then
        if [ "$(readlink "$link_path")" != "$skill_dir" ]; then
            echo "conflict at $link_path" >&2
            exit 1
        fi
    elif [ -e "$link_path" ]; then
        echo "conflict at $link_path" >&2
        exit 1
    fi
done

for skill_dir in "$skills_root"/*; do
    [ -d "$skill_dir" ] || continue
    [ -f "$skill_dir/SKILL.md" ] || continue
    name=$(basename "$skill_dir")
    link_path=$destination/$name
    [ -L "$link_path" ] && continue
    ln -s "$skill_dir" "$link_path"
done
