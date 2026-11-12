#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source=${XR_SOURCE_DIR:-"$root/../out/xr-kernel-source"}
if [ ! -d "$source/.git" ]; then
 if [ -n "${XR_UPSTREAM_REPO:-}" ]; then python3 "$root/tools/prepare-source.py" --output "$source" --upstream-repo "$XR_UPSTREAM_REPO"; else python3 "$root/tools/prepare-source.py" --output "$source"; fi
fi
expected=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["commit"])' "$root/upstream.json")
actual=$(git -C "$source" rev-parse HEAD)
[ "$actual" = "$expected" ] || { echo 'Kernel source differs from the canonical commit lock' >&2; exit 1; }
if ! git -C "$source" diff --quiet -- arch drivers fs include init kernel lib mm net sound; then
 echo 'Uncommitted kernel implementation changes cannot enter a locked package build' >&2
 exit 1
fi
exec "$source/packaging/build-in-source.sh"
