#!/usr/bin/env python3
"""Copy this overlay into an explicitly selected, private void-packages checkout."""

import argparse
from pathlib import Path
import shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("checkout", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
checkout = args.checkout.resolve()
if not (checkout / "xbps-src").is_file() or not (checkout / "common/shlibs").is_file():
    parser.error("checkout must contain the official xbps-src and common/shlibs")

for source in sorted((root / "srcpkgs").iterdir()):
    target = checkout / "srcpkgs" / source.name
    if source.is_symlink():
        if target.is_symlink() and target.readlink() == source.readlink():
            continue
        if target.exists() or target.is_symlink():
            parser.error(f"refusing to replace an existing path: {target}")
        target.symlink_to(source.readlink(), target_is_directory=True)
        continue
    if (target / "template").exists() and "AbyssWM/" not in (target / "template").read_text():
        parser.error(f"refusing to replace unrelated template: {target}")
    shutil.copytree(source, target, dirs_exist_ok=True)

shlibs = checkout / "common/shlibs"
additions = (root / "shlibs").read_text().splitlines()
names = {line.split()[0] for line in additions}
existing = [line for line in shlibs.read_text().splitlines()
            if not line.split() or line.split()[0] not in names]
shlibs.write_text("\n".join(existing + additions) + "\n")
print(f"Prepared {len(list((root / 'srcpkgs').iterdir()))} templates in {checkout}")
