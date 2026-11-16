#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
build_dir=${XR_BUILD_DIR:-"$root/../out/kernel"}
mkdir -p "$build_dir"
export ARCH=${ARCH:-arm64}
export CROSS_COMPILE=${CROSS_COMPILE:-aarch64-linux-gnu-}
export KBUILD_BUILD_USER=xr KBUILD_BUILD_HOST=build
export LOCALVERSION=${LOCALVERSION-}
export SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH:-0}
python3 - "$root" "$build_dir" <<'PY'
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

root, build = (Path(value).resolve() for value in sys.argv[1:])
lock = json.loads((root / 'packaging/source-lock.json').read_text())
if os.environ.get('XR_KERNEL_DEVICE', lock['device']) != lock['device']:
    raise SystemExit('Requested device differs from the prepared source lock')
commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'],
                                 text=True).strip()
if commit != lock['commit']:
    raise SystemExit('Kernel source differs from the prepared commit lock')
inputs = [lock['config'], *lock.get('config_fragments', [])]
for name in inputs:
    path = Path(name)
    if path.is_absolute() or '..' in path.parts or not (root / path).is_file():
        raise SystemExit('Invalid locked kernel configuration path: ' + name)
subprocess.run(['git', '-C', str(root), 'diff', 'HEAD', '--exit-code', '--',
                *inputs], check=True)
config = build / '.config'
shutil.copyfile(root / lock['config'], config)
fragments = [str(root / name) for name in lock.get('config_fragments', [])]
if fragments:
    subprocess.run([str(root / 'scripts/kconfig/merge_config.sh'), '-m',
                    '-O', str(build), str(config), *fragments], check=True)
PY
make -C "$root" O="$build_dir" olddefconfig
make -C "$root" O="$build_dir" KDEB_SOURCENAME=linux-xr KDEB_PKGVERSION="${XR_DEB_VERSION:-7.3.0+xr1}" -j"${JOBS:-4}" bindeb-pkg
python3 "$root/packaging/build-uapi-deb.py" --output "$build_dir/../packages" --version "${XR_DEB_VERSION:-7.3.0+xr1}" --kernel-release "$(make -s -C "$root" O="$build_dir" kernelrelease)"
