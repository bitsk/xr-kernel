#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Package an offline XR2 camera kernel without changing a root or device.

The supplied baseline contributes boot transport, root selection, local identity
and ramdisk. Only the CAMSS resource properties come from the built board DTB.
"""
import argparse
import hashlib
import json
import lzma
from pathlib import Path
import shutil
import struct
import subprocess


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def run(*args):
    return subprocess.check_output([str(arg) for arg in args])


def unpack(image, destination):
    return [part.decode() for part in run('unpack_bootimg', '--boot_img', image,
            '--out', destination, '--format', 'mkbootimg', '-0').rstrip(b'\0').split(b'\0')]


def properties(dtb, node):
    return {name: bytes(int(value, 16) for value in run('fdtget', '-t', 'bx', dtb, node, name).split())
            for name in run('fdtget', '-p', dtb, node).decode().splitlines()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--baseline-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source, build, baseline = args.source.resolve(), args.build.resolve(), args.baseline.resolve()
    if args.output.exists():
        parser.error('Choose a new output directory')
    if sha(baseline) != args.baseline_sha256:
        parser.error('Baseline digest mismatch')
    if run('git', '-C', source, 'status', '--porcelain').strip():
        parser.error('The kernel source must be committed and clean')
    commit = run('git', '-C', source, 'rev-parse', 'HEAD').decode().strip()
    image = build / 'arch/arm64/boot/Image'
    source_dtb = build / 'arch/arm64/boot/dts/qcom/sm8250-iqiyi-a081.dtb'
    memory_bytes = struct.unpack_from('<Q', image.read_bytes(), 16)[0]
    if not 0 < memory_bytes <= 0xf80000:
        parser.error('Kernel overlaps the retained ABL initramfs address')
    out = args.output.resolve()
    out.mkdir(parents=True)
    boot_args = unpack(baseline, out / 'baseline')
    dtb = out / 'boot.dtb'
    shutil.copyfile(out / 'baseline/dtb', dtb)
    node = '/soc@0/camss@ac6a000'
    keep = properties(dtb, node)
    selected = properties(source_dtb, node)
    names = ('compatible', 'reg', 'reg-names', 'interrupts', 'interrupt-names')
    if selected['compatible'] != b'qcom,sxr2130-camss\0':
        parser.error('Expected an XR2 camera resource DTB')
    if keep['iommus'] != selected['iommus']:
        parser.error('The baseline camera IOMMU assignment differs')
    for name in names:
        run('fdtput', '-t', 'bx', dtb, node, name, *[f'{byte:02x}' for byte in selected[name]])
    merged = properties(dtb, node)
    if any(merged[name] != value for name, value in keep.items() if name not in names):
        raise ValueError('Unexpected camera property change')
    # Recompress the complete existing newc archive; all file, identity, device
    # node and root-selector contents are retained byte for byte.
    archive = lzma.decompress((out / 'baseline/ramdisk').read_bytes())
    if not archive.startswith(b'070701') or b'TRAILER!!!\0' not in archive:
        raise ValueError('Expected a newc initramfs')
    ramdisk = out / 'initramfs.cpio.xz'
    ramdisk.write_bytes(lzma.compress(archive, format=lzma.FORMAT_XZ,
                                    check=lzma.CHECK_CRC32, preset=9))
    if lzma.decompress(ramdisk.read_bytes()) != archive or ramdisk.stat().st_size >= 0xf00000:
        raise ValueError('Initramfs integrity or size check failed')
    shutil.copyfile(image, out / 'Image')
    shutil.copyfile(build / '.config', out / 'kernel.config')
    shutil.copyfile(source_dtb, out / 'source.dtb')
    for option, value in (('--kernel', out / 'Image'), ('--ramdisk', ramdisk), ('--dtb', dtb)):
        boot_args[boot_args.index(option) + 1] = str(value)
    candidate = out / 'recovery-xr2-cameras.img'
    run('mkbootimg', *boot_args, '--output', candidate)
    if candidate.stat().st_size > baseline.stat().st_size:
        raise ValueError('Candidate exceeds the baseline partition image')
    padded = out / 'recovery-xr2-cameras.bin'
    padded.write_bytes(candidate.read_bytes().ljust(baseline.stat().st_size, b'\0'))
    unpack(padded, out / 'roundtrip')
    for name, expected in (('kernel', out / 'Image'), ('ramdisk', ramdisk), ('dtb', dtb),
                           ('recovery_dtbo', out / 'baseline/recovery_dtbo')):
        if sha(out / 'roundtrip' / name) != sha(expected):
            raise ValueError('Boot roundtrip mismatch: ' + name)
    result = dict(source_commit=commit, kernel_release=(build / 'include/config/kernel.release').read_text().strip(),
                  kernel_memory_bytes=memory_bytes, baseline_sha256=sha(baseline),
                  camss_properties_replaced=list(names), initramfs_repacked=True,
                  initramfs_contents_unchanged=True, boot_roundtrip_verified=True,
                  baseline_promoted=False, device_tested=False, device_accessed=False,
                  files_sha256={path.name: sha(path) for path in out.iterdir() if path.is_file()})
    (out / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
