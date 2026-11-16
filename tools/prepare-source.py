#!/usr/bin/env python3
"""Prepare the selected device's exact canonical kernel source and build lock."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess


root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--upstream-repo', type=Path)
parser.add_argument('--device', choices=('a081', 'vr700'),
                    default=os.environ.get('XR_KERNEL_DEVICE', 'a081'))
args = parser.parse_args()
if args.device not in ('a081', 'vr700'):
    parser.error('Unknown XR_KERNEL_DEVICE')
lock_path = (root / 'upstream.json' if args.device == 'a081'
             else root / 'devices' / args.device / 'upstream.json')
lock = json.loads(lock_path.read_text())
out = args.output.resolve()
if out.exists():
    parser.error('Use a new output directory')
source = str(args.upstream_repo.resolve()) if args.upstream_repo else lock['repository']
command = ['git', 'clone', '--no-checkout']
command += ['--shared'] if args.upstream_repo else ['--filter=blob:none']
subprocess.run(command + [source, str(out)], check=True)
subprocess.run(['git', '-C', str(out), 'checkout', '-B',
                'xr/adaptation', lock['commit']], check=True)
for key in ('user.name', 'user.email'):
    value = subprocess.check_output(['git', '-C', str(root), 'config', '--get', key],
                                    text=True).strip()
    subprocess.run(['git', '-C', str(out), 'config', key, value], check=True)
patches = []
if lock.get('patch_series'):
    patches = [str(root / 'patches' / name)
               for name in (root / lock['patch_series']).read_text().splitlines()
               if name.strip()]
    if patches:
        subprocess.run(['git', '-C', str(out), 'am', *patches], check=True)
for directory in ('packaging', 'debian'):
    if (root / directory).exists():
        shutil.copytree(root / directory, out / directory, dirs_exist_ok=True)
for header in (root / 'include/uapi').rglob('*.h'):
    relative = header.relative_to(root / 'include/uapi')
    if header.read_bytes() != (out / 'include/uapi' / relative).read_bytes():
        raise ValueError('Exported UAPI snapshot differs from canonical kernel')
prepared_lock = dict(lock, device=args.device)
(out / 'packaging/source-lock.json').write_text(
    json.dumps(prepared_lock, indent=2) + '\n')
print(json.dumps({'source': str(out), 'upstream': lock['commit'],
                  'device': args.device, 'patches': len(patches),
                  'device_validated': False}))
