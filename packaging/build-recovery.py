#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Assemble a recovery candidate from explicit kernel, ramdisk and stock inputs.

This performs no device operations. Boot transport matching values are private
inputs established for the target bootloader, separate from board wiring.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4194304), b''):
            h.update(block)
    return h.hexdigest()


def run(*args):
    return subprocess.check_output([str(x) for x in args])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('source', 'artifacts', 'ramdisk', 'baseline', 'transport', 'output'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--ramdisk-sha256', required=True)
    p.add_argument('--baseline-sha256', required=True)
    a = p.parse_args()
    if a.output.exists():
        p.error('Use a new output directory')
    if sha(a.baseline) != a.baseline_sha256 or sha(a.ramdisk) != a.ramdisk_sha256:
        p.error('Baseline or initramfs digest mismatch')
    source = a.source.resolve()
    commit = run('git', '-C', source, 'rev-parse', 'HEAD').decode().strip()
    if run('git', '-C', source, 'status', '--porcelain').strip():
        p.error('Kernel source must be committed and clean')
    if (a.artifacts / 'source-commit').read_text().strip() != commit:
        p.error('Kernel artifacts do not select the current source commit')
    subprocess.run(['sha256sum', '--check', 'SHA256SUMS'], cwd=a.artifacts,
                   check=True, stdout=subprocess.DEVNULL)
    transport = json.loads(a.transport.read_text())
    image = a.artifacts / 'Image'
    footprint = struct.unpack_from('<Q', image.read_bytes(), 16)[0]
    # These offsets are the established SM8250 ABL transport contract. Reject
    # another header instead of silently applying them to a different loader.
    header = a.baseline.read_bytes()[:4096]
    if (header[:8] != b'ANDROID!' or struct.unpack_from('<I', header, 40)[0] != 2
            or struct.unpack_from('<I', header, 36)[0] != 4096
            or struct.unpack_from('<I', header, 12)[0] != 0x8000
            or struct.unpack_from('<I', header, 20)[0] != 0x1000000
            or struct.unpack_from('<Q', header, 1652)[0] != 0x1f00000):
        p.error('Unrecognized boot header layout')
    if not 0 < footprint <= 0xf80000 or a.ramdisk.stat().st_size >= 0xf00000:
        p.error('Kernel/initramfs exceed the verified ABL load windows')
    out = a.output.resolve()
    out.mkdir(parents=True)
    args = [x.decode() for x in run('unpack_bootimg', '--boot_img', a.baseline,
            '--out', out / 'stock', '--format', 'mkbootimg', '-0').rstrip(b'\0').split(b'\0')]
    board = out / 'board.dtb'
    shutil.copyfile(a.artifacts / 'source.dtb', board)
    compatibles = run('fdtget', '-t', 's', board, '/', 'compatible').decode().split()
    if transport['compatible'] not in compatibles:
        p.error('Board DTB does not match the selected device')
    for prop in ('qcom,msm-id', 'qcom,pmic-id'):
        values = transport[prop]
        if not values or any(type(v) is not int or not 0 <= v <= 0xffffffff for v in values):
            p.error('Invalid boot transport cells')
        run('fdtput', '-t', 'x', board, '/', prop, *[f'{v:x}' for v in values])
    cmdline = transport['cmdline']
    run('fdtput', '-t', 's', board, '/chosen', 'bootargs', cmdline)
    noop = out / 'noop.dts'
    noop.write_text('/dts-v1/; /plugin/;\n/ { fragment@0 { target-path = "/"; __overlay__ {}; }; };\n')
    overlay = out / 'noop.dtbo'
    run('dtc', '-I', 'dts', '-O', 'dtb', '-o', overlay, noop)
    payload = overlay.read_bytes()
    table = out / 'recovery-dtbo.img'
    table.write_bytes(struct.pack('>8I', 0xd7b7ab1e, 64 + len(payload), 32, 32, 1, 32, 4096, 0)
                      + struct.pack('>8I', len(payload), 64, 0, 0, 0, 0, 0, 0) + payload)
    run('fdtoverlay', '-i', board, '-o', out / 'overlay-check.dtb', overlay)
    if run('dtc', '-I', 'dtb', '-O', 'dts', '-s', board) != run(
            'dtc', '-I', 'dtb', '-O', 'dts', '-s', out / 'overlay-check.dtb'):
        p.error('Recovery overlay altered the board description')
    for option, value in (('--kernel', image.resolve()), ('--ramdisk', a.ramdisk.resolve()),
                          ('--dtb', board), ('--recovery_dtbo', table), ('--cmdline', cmdline)):
        if option in args:
            args[args.index(option) + 1] = str(value)
        else:
            args.extend((option, str(value)))
    candidate = out / 'recovery.img'
    run('mkbootimg', *args, '--output', candidate)
    if candidate.stat().st_size > a.baseline.stat().st_size:
        p.error('Candidate exceeds the original recovery partition size')
    padded = out / 'recovery.bin'
    padded.write_bytes(candidate.read_bytes().ljust(a.baseline.stat().st_size, b'\0'))
    run('unpack_bootimg', '--boot_img', padded, '--out', out / 'roundtrip')
    for name, original in (('kernel', image), ('ramdisk', a.ramdisk), ('dtb', board), ('recovery_dtbo', table)):
        if sha(out / 'roundtrip' / name) != sha(original):
            p.error('Boot image roundtrip mismatch: ' + name)
    result = {'source_commit': commit, 'compatible': transport['compatible'],
              'baseline_sha256': sha(a.baseline), 'ramdisk_sha256': sha(a.ramdisk),
              'transport_sha256': sha(a.transport), 'kernel_memory_bytes': footprint,
              'recovery_sha256': sha(padded), 'bytes': padded.stat().st_size,
              'roundtrip_verified': True, 'overlay_noop_verified': True,
              'device_tested': False, 'device_write_performed': False}
    (out / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
