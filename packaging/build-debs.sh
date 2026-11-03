#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source=${XR_SOURCE_DIR:-"$root/../out/xr-kernel-source"}
if [ ! -d "$source/.git" ]; then
 if [ -n "${XR_UPSTREAM_REPO:-}" ]; then python3 "$root/tools/prepare-source.py" --output "$source" --upstream-repo "$XR_UPSTREAM_REPO"; else python3 "$root/tools/prepare-source.py" --output "$source"; fi
fi
exec "$source/packaging/build-in-source.sh"
