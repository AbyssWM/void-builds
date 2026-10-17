#!/usr/bin/env python3
"""Build the prepared Void overlay in order; stop at the first failed package."""

import argparse
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("checkout", type=Path)
parser.add_argument("--logs", type=Path, required=True)
parser.add_argument("--jobs", type=int, default=2)
parser.add_argument("packages", nargs="*")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
checkout = args.checkout.resolve()
args.logs.mkdir(parents=True, exist_ok=True)
if args.jobs < 1:
    parser.error("--jobs must be positive")
catalog = json.loads((root / "catalog.json").read_text())
sources = json.loads((root / "sources.json").read_text())
names = [catalog["packages"][p["repo"]]["name"] for p in sources["packages"]]
if args.packages:
    unknown = set(args.packages) - set(names)
    if unknown:
        parser.error(f"unknown packages: {sorted(unknown)}")
    names = [name for name in names if name in args.packages]
receipt = []
for name in names:
    log = (args.logs / f"{name}.log").resolve()
    print(f"Building {name}; log: {log}", flush=True)
    with log.open("w") as output:
        result = subprocess.run(["./xbps-src", "-n", f"-j{args.jobs}", "pkg", name],
                                cwd=checkout, stdout=output, stderr=subprocess.STDOUT)
    receipt.append({"package": name, "exit_code": result.returncode, "log": log.name})
    (args.logs / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if result.returncode:
        print(f"FAILED: {name}\n" + "\n".join(log.read_text().splitlines()[-30:]), flush=True)
        raise SystemExit(result.returncode)
    print(f"Built {name}", flush=True)
