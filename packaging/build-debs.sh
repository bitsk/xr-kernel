#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
device=${XR_KERNEL_DEVICE:-a081}
while [ "$#" -gt 0 ]; do
 case "$1" in
  --device) [ "$#" -ge 2 ] || { echo '--device requires a model' >&2; exit 1; }; device=$2; shift 2 ;;
  --help) echo 'Usage: build-debs.sh [--device a081|vr700] (or XR_KERNEL_DEVICE)'; exit 0 ;;
  *) echo "Unknown argument: $1" >&2; exit 1 ;;
 esac
done
case "$device" in
 a081) lock="$root/upstream.json" ;;
 vr700) lock="$root/devices/vr700/upstream.json" ;;
 *) echo "Unknown kernel device: $device" >&2; exit 1 ;;
esac
export XR_KERNEL_DEVICE="$device"
: "${XR_SOURCE_DIR:?Set XR_SOURCE_DIR to a new external preparation directory; normal builds use xr-build-components}"
source=$(realpath -m -- "$XR_SOURCE_DIR")
workspace=$(dirname -- "$root")
case "$source" in "$workspace"|"$workspace"/*) echo "Prepared sources must be outside the canonical source workspace" >&2; exit 1;; esac
if [ -e "$source" ]; then echo "Use a new preparation directory; resume locked integration builds with xr-build-components --resume" >&2; exit 1; fi
if [ ! -d "$source/.git" ]; then
 if [ -n "${XR_UPSTREAM_REPO:-}" ]; then python3 "$root/tools/prepare-source.py" --device "$device" --output "$source" --upstream-repo "$XR_UPSTREAM_REPO"; else python3 "$root/tools/prepare-source.py" --device "$device" --output "$source"; fi
fi
expected=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["commit"])' "$lock")
actual=$(git -C "$source" rev-parse HEAD)
[ "$actual" = "$expected" ] || { echo 'Kernel source differs from the canonical commit lock' >&2; exit 1; }
if ! git -C "$source" diff HEAD --quiet -- arch devices drivers fs include init kernel lib mm net sound; then
 echo 'Uncommitted kernel implementation changes cannot enter a locked package build' >&2
 exit 1
fi
exec "$source/packaging/build-in-source.sh"
