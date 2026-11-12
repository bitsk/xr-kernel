#!/usr/bin/env python3
import argparse,shutil,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);p.add_argument('--version',default='7.3.0+xr1');p.add_argument('--kernel-release');a=p.parse_args();r=Path(__file__).resolve().parents[1];a.output.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as temp:
 root=Path(temp);dest=root/'usr/include/xr-kernel/linux';dest.mkdir(parents=True)
 for name in ['a081-nordic.h','ov7251.h','qcom-camss-timing.h']:shutil.copy2(r/'include/uapi/linux'/name,dest/name)
 (root/'usr/include/xr-kernel/misc').mkdir();shutil.copy2(r/'include/uapi/misc/fastrpc.h',root/'usr/include/xr-kernel/misc/fastrpc.h')
 (root/'DEBIAN').mkdir();(root/'DEBIAN/control').write_text(f'Package: xr-kernel-uapi-dev\nVersion: {a.version}\nArchitecture: all\nMaintainer: openKylin XR SIG <xr@lists.openkylin.top>\nSection: libdevel\nPriority: optional\nDescription: XR kernel userspace interface headers\n')
 subprocess.run(['dpkg-deb','--root-owner-group','--build',str(root),str(a.output/f'xr-kernel-uapi-dev_{a.version}_all.deb')],check=True)

if a.kernel_release:
 with tempfile.TemporaryDirectory() as temp:
  root=Path(temp);(root/'DEBIAN').mkdir()
  (root/'DEBIAN/control').write_text(f'Package: linux-image-xr-arm64\nVersion: {a.version}\nArchitecture: arm64\nMaintainer: openKylin XR SIG <xr@lists.openkylin.top>\nSection: metapackages\nPriority: optional\nDepends: linux-image-{a.kernel_release} (= {a.version})\nDescription: Independent XR ARM64 kernel selection\n')
  subprocess.run(['dpkg-deb','--root-owner-group','--build',str(root),str(a.output/f'linux-image-xr-arm64_{a.version}_arm64.deb')],check=True)
