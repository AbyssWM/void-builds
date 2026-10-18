#!/usr/bin/env python3
"""Move package pins to the newest green commit of each Abyss source repository.

For every package in sources.json: take the newest commit on the source repository's main branch,
skip it unless its CI finished green and it changes more than documentation, then download the
archive, record its checksums in sources.json and update this repository's recipes. Packages with
local patches (patches/<name>/) are only reported, since a patch may be upstream by then.

The same file is used in all package repositories; the recipe format is detected from the
repository layout (Arch, Fedora, Debian/Ubuntu, Void, Gentoo). Prints one line per updated
package; exits 0 whether or not anything changed.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
API = "https://api.github.com/repos/AbyssWM"
DOC_ONLY = re.compile(r"(\.md$|^docs/|^\.github/|^LICENSE|^LICENSES|^README)")


def api(path):
    # in CI the workflow token; locally the logged-in gh CLI (unauthenticated requests run out fast)
    if not os.environ.get("GITHUB_TOKEN") and subprocess.run(["gh", "auth", "status"], capture_output=True).returncode == 0:
        return json.loads(subprocess.run(["gh", "api", "/repos/AbyssWM" + path], capture_output=True, check=True, text=True).stdout)
    request = urllib.request.Request(API + path, headers={"Accept": "application/vnd.github+json"})
    if token := os.environ.get("GITHUB_TOKEN"):
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def green(repo, sha):
    """CI finished and passed (a commit without any checks counts as green)."""
    runs = api(f"/{repo}/commits/{sha}/check-runs?per_page=100")["check_runs"]
    return all(r["status"] == "completed" and r["conclusion"] in ("success", "skipped", "neutral") for r in runs)


def only_docs(repo, old, new):
    files = api(f"/{repo}/compare/{old}...{new}").get("files", [])
    return bool(files) and all(DOC_ONLY.search(f["filename"]) for f in files)


def archive(url):
    with urllib.request.urlopen(url, timeout=300) as response:
        data = response.read()
    return {
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "sha512": hashlib.sha512(data).hexdigest(),
        "blake2b": hashlib.blake2b(data).hexdigest(),
    }


def replace(path, pairs):
    text = path.read_text()
    for old, new in pairs:
        if old not in text:
            sys.exit(f"{path}: expected to find {old!r}")
        text = text.replace(old, new)
    path.write_text(text)


def date_of(entry, sources):
    return entry.get("snapshot_date", sources["snapshot_date"])


# ---- recipe formats -------------------------------------------------------------------------


def update_arch(name, old, new, sources):
    for f in ("PKGBUILD", ".SRCINFO"):
        replace(ROOT / "packages" / name / f, [
            (old["commit"], new["commit"]),
            (f'{old["version"]}.r{date_of(old, sources)}.g{old["commit"][:7]}', f'{new["version"]}.r{new["snapshot_date"]}.g{new["commit"][:7]}'),
            (old["sha256"], new["sha256"]),
        ])
        text = (ROOT / "packages" / name / f).read_text()
        text = re.sub(r"(?m)^(\s*pkgrel ?= ?)\d+$", r"\g<1>1", text)
        (ROOT / "packages" / name / f).write_text(text)


def update_fedora(name, old, new, sources):
    spec = ROOT / "specs" / f"{name}.spec"
    pairs = [
        (old["commit"], new["commit"]),
        (f'{date_of(old, sources)}git{old["commit"][:7]}', f'{new["snapshot_date"]}git{new["commit"][:7]}'),
        (old["sha256"], new["sha256"]),
    ]
    if old["version"] != new["version"]:
        text = spec.read_text()
        text = re.sub(r"(?m)^(Version:\s*)\S+$", r"\g<1>" + new["version"], text)
        spec.write_text(text)
    replace(spec, pairs)


def update_debian(name, old, new, sources, subject):
    base = ROOT / "packages" / name / "debian"
    changelog = base / "changelog"
    first = changelog.read_text().splitlines()[0]
    match = re.match(r"^(\S+) \((\S+)\) (\S+);", first)
    if not match:
        sys.exit(f"{changelog}: cannot read the first entry")
    source, version, dist = match.groups()
    suffix = version[version.index("~"):] if "~" in version else ""
    newversion = f'{new["version"]}+git{new["snapshot_date"]}.{new["commit"][:7]}-1{suffix}'
    stamp = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    maintainer = sources["maintainer"]
    entry = (f"{source} ({newversion}) {dist}; urgency=medium\n\n"
             f"  * Update to {new['repo']} {new['commit'][:7]}: {subject}\n\n"
             f" -- {maintainer['name']} <{maintainer['email']}>  {stamp}\n\n")
    changelog.write_text(entry + changelog.read_text())
    copyright_ = base / "copyright"
    if old["commit"] in copyright_.read_text():
        replace(copyright_, [(old["commit"], new["commit"])])


def regenerate(tool):
    subprocess.run([sys.executable, "-I", str(ROOT / "tools" / tool)], check=True, stdout=subprocess.DEVNULL)


def update_gentoo_manifests(updated, sources):
    """generate.py writes the ebuilds; the DIST lines of the Manifests are written here."""
    catalog = json.loads((ROOT / "catalog.json").read_text())
    for entry in updated:
        package = catalog["packages"][entry["repo"]]
        directory = ROOT / package["category"] / package["name"]
        for ebuild in directory.glob("*.ebuild"):
            if f'_p{entry["snapshot_date"]}' not in ebuild.name:
                ebuild.unlink()
        distname = f'{package["name"]}-{entry["version"]}_p{entry["snapshot_date"]}.tar.gz'
        manifest = directory / "Manifest"
        lines = [l for l in manifest.read_text().splitlines() if not l.startswith(f'DIST {package["name"]}-')]
        lines.insert(0, f'DIST {distname} {entry["size"]} BLAKE2B {entry["blake2b"]} SHA512 {entry["sha512"]}')
        manifest.write_text("\n".join(lines) + "\n")


def layout():
    if (ROOT / "specs").is_dir():
        return "fedora"
    if (ROOT / "srcpkgs").is_dir():
        return "void"
    if (ROOT / "profiles").is_dir():
        return "gentoo"
    if any((ROOT / "packages").glob("*/PKGBUILD")):
        return "arch"
    if any((ROOT / "packages").glob("*/debian/changelog")):
        return "debian"
    sys.exit("unknown repository layout")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="only report what would be updated")
    args = parser.parse_args()

    kind = layout()
    sources_path = ROOT / "sources.json"
    sources = json.loads(sources_path.read_text())
    catalog = json.loads((ROOT / "catalog.json").read_text())
    updated = []

    for entry in sources["packages"]:
        repo = entry["repo"]
        head = api(f"/{repo}/commits/main")
        sha = head["sha"]
        if sha == entry["commit"]:
            continue
        if not green(repo, sha):
            print(f"{repo}: {sha[:7]} not green yet, keeping {entry['commit'][:7]}", file=sys.stderr)
            continue
        if only_docs(repo, entry["commit"], sha):
            continue
        name = catalog["packages"][repo]["name"]
        # local patches may be upstream by now or no longer apply; those packages are moved by hand
        if (ROOT / "patches" / name).is_dir():
            print(f"::warning::{repo}: {sha[:7]} is newer, but {name} carries local patches; update it by hand")
            continue
        if args.dry_run:
            print(f"{repo}: {entry['commit'][:7]} -> {sha[:7]}")
            continue

        old = dict(entry)
        date = datetime.fromisoformat(head["commit"]["committer"]["date"].replace("Z", "+00:00"))
        url = f"https://github.com/AbyssWM/{repo}/archive/{sha}.tar.gz"
        entry.update(commit=sha, url=url, filename=f"{repo}-{sha}.tar.gz", snapshot_date=date.strftime("%Y%m%d"), **archive(url))
        subject = head["commit"]["message"].splitlines()[0]

        if kind == "arch":
            update_arch(name, old, entry, sources)
        elif kind == "fedora":
            update_fedora(name, old, entry, sources)
        elif kind == "debian":
            update_debian(name, old, entry, sources, subject)
        updated.append(entry)
        print(f"{repo}: {old['commit'][:7]} -> {sha[:7]} ({subject})")

    if not updated or args.dry_run:
        return
    sources_path.write_text(json.dumps(sources, indent=2, ensure_ascii=False) + "\n")
    if kind == "void":
        regenerate("generate.py")
    elif kind == "gentoo":
        regenerate("generate.py")
        update_gentoo_manifests(updated, sources)


if __name__ == "__main__":
    main()
