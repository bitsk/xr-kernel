#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
build_dir=${XR_BUILD_DIR:-"$root/../out/kernel"}
mkdir -p "$build_dir"
cp "$root/devices/a081/config/kernel.config" "$build_dir/.config"
export ARCH=${ARCH:-arm64}
export CROSS_COMPILE=${CROSS_COMPILE:-aarch64-linux-gnu-}
export KBUILD_BUILD_USER=xr KBUILD_BUILD_HOST=build
export SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH:-0}
make -C "$root" O="$build_dir" olddefconfig
make -C "$root" O="$build_dir" KDEB_SOURCENAME=linux-xr KDEB_PKGVERSION="${XR_DEB_VERSION:-7.3.0+xr1}" -j"${JOBS:-4}" bindeb-pkg
python3 "$root/packaging/build-uapi-deb.py" --output "$build_dir/../packages" --version "${XR_DEB_VERSION:-7.3.0+xr1}"
