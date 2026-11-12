#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
build_dir=${XR_BUILD_DIR:-"$root/../out/kernel"}
mkdir -p "$build_dir"
cp "$root/devices/a081/config/kernel.config" "$build_dir/.config"
export ARCH=${ARCH:-arm64}
export CROSS_COMPILE=${CROSS_COMPILE:-aarch64-linux-gnu-}
export KBUILD_BUILD_USER=xr KBUILD_BUILD_HOST=build
export LOCALVERSION=${LOCALVERSION-}
export SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH:-0}
"$root/scripts/kconfig/merge_config.sh" -m -O "$build_dir" "$build_dir/.config" "$root/devices/a081/config/xr-cameras.config" "$root/devices/a081/config/usb-pd-5v.config" "$root/devices/a081/config/xr-scheduling.config"
make -C "$root" O="$build_dir" olddefconfig
make -C "$root" O="$build_dir" KDEB_SOURCENAME=linux-xr KDEB_PKGVERSION="${XR_DEB_VERSION:-7.3.0+xr1}" -j"${JOBS:-4}" bindeb-pkg
python3 "$root/packaging/build-uapi-deb.py" --output "$build_dir/../packages" --version "${XR_DEB_VERSION:-7.3.0+xr1}" --kernel-release "$(make -s -C "$root" O="$build_dir" kernelrelease)"
