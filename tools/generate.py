#!/usr/bin/env python3
"""Regenerate this distribution's pinned Abyss recipes."""

import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def void(package, catalog, sources):
    name = package["name"]
    deps = [catalog["dependencies"][key]["void"] for key in package["dependencies"]]
    develdeps = list(deps)
    for dependency in package["internal"]:
        target = next(p for p in sources["packages"] if p["name"] == dependency)
        deps.append(dependency + ("-devel" if target.get("library") else ""))
        develdeps.append(deps[-1])
    builddeps = ["pkg-config"]
    builddeps += [catalog["dependencies"][key]["void"] for key in package.get("build_dependencies", [])]
    builddeps += package.get("build_internal", [])
    options = list(package.get("cmake", []))
    if package["build_system"] == "cmake":
        options = ["-DBUILD_TESTING=OFF", "-DFETCHCONTENT_FULLY_DISCONNECTED=ON"] + options
    if name == "abyssland":
        options += ['-DABYSS_CONFIG=${wrksrc}/${build_wrksrc}/config.def.hpp', '-DFETCHCONTENT_SOURCE_DIR_GLAZE=${wrksrc}/glaze-7.2.0', '-DNO_SYSTEMD=ON', '-DNO_UWSM=ON']
    if name == "abysspaper":
        options += ['-DABYSS_CONFIG_DIR=${wrksrc}/empty-config']
    version = package["version"] + "." + sources["snapshot_date"]
    text = f'''# SPDX-License-Identifier: 0BSD
# Template file for '{name}'
# Pinned development snapshot; not an upstream release.
pkgname={name}
version={version}
revision=1
_commit={package["commit"]}
wrksrc="{package["repo"]}-${{_commit}}"
build_style={package["build_system"]}
'''
    if options:
        text += 'configure_args="' + "\n ".join(options) + '"\n'
    text += 'hostmakedepends="' + " ".join(sorted(set(builddeps))) + '"\n'
    if deps:
        text += 'makedepends="' + " ".join(sorted(set(deps))) + '"\n'
    runtime = package.get("runtime", {}).get("void", [])
    if runtime:
        text += 'depends="' + " ".join(runtime) + '"\n'
    text += f'''short_desc="{package["description"]}"
maintainer="{sources["maintainer"]["name"]} <{sources["maintainer"]["email"]}>"
license="{package["license"]}"
homepage="https://github.com/AbyssWM/{package["repo"]}"
distfiles="${{homepage}}/archive/${{_commit}}.tar.gz"
checksum={package["sha256"]}
'''
    if name == "abyssland":
        extra = sources["extras"]["glaze"]
        text += 'wrksrc="${pkgname}-${version}"\n'
        text += f'build_wrksrc="{package["repo"]}-${{_commit}}"\n'
        text += f'distfiles+=" {extra["url"]}>{extra["filename"]}"\nchecksum+=" {extra["sha256"]}"\n'
    directory = ROOT / "srcpkgs" / name
    for patch in package.get("patches", []):
        directory.joinpath("patches").mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / "patches" / name / patch, directory / "patches" / patch)
    text += '\npost_install() {\n\tvlicense LICENSE\n'
    if name == "abyssland":
        text += '\tvlicense "${wrksrc}/glaze-7.2.0/LICENSE" glaze-LICENSE\n'
    text += '}\n'
    if package.get("library"):
        text += f'''
{name}-devel_package() {{
\tdepends="${{sourcepkg}}>=${{version}}_${{revision}} {" ".join(sorted(set(develdeps)))}"
\tshort_desc+=" - development files"
\tpkg_install() {{
\t\tvmove usr/include
\t\tvmove "usr/lib/*.so"
\t\tvmove usr/lib/pkgconfig
'''
        if name == "abysstoolkit":
            text += '\t\tvmove usr/share/abysstoolkit/cmake\n'
        text += '\t}\n}\n'
    write(directory / "template", text)
    if package.get("library"):
        link = ROOT / "srcpkgs" / (name + "-devel")
        if not link.is_symlink():
            link.symlink_to(name, target_is_directory=True)


def main():
    sources = json.loads((ROOT / "sources.json").read_text())
    catalog = json.loads((ROOT / "catalog.json").read_text())
    for package in sources["packages"]:
        package.update(catalog["packages"][package["repo"]])
    for package in sources["packages"]:
        void(package, catalog, sources)
    write(ROOT / "shlibs", "\n".join(
        f'lib{p["name"]}.so.{p["soname"]} {p["name"]}-{p["version"]}.{sources["snapshot_date"]}_1'
        for p in sources["packages"] if p.get("library")) + "\n")


if __name__ == "__main__":
    main()
