# Abyss Void builds

Experimental Void Linux package templates for all 17 Abyss repositories.
These are third-party development snapshots, not packages accepted into Void's
official repository. Remaining package builds are still being validated.

`sources.json` pins the public archives and their hashes. `catalog.json` records
dependencies and package names. The seven libraries have separate `-devel`
packages. `shlibs` supplies their SONAME mappings. The compositor compiles the
public default config, never the packager's personal configuration.

Use a dedicated checkout of the official
[void-packages](https://github.com/void-linux/void-packages) build system:

```sh
python3 tools/prepare.py /path/to/void-packages
```

Configure `XBPS_CHROOT_CMD=bwrap` in that checkout's `etc/conf` and run its
`./xbps-src binary-bootstrap` as an ordinary user. Then, from this repository:

```sh
python3 tools/build.py /path/to/void-packages --logs out/logs --jobs 2
```

The driver builds in dependency order and stops on the first failure. It uses
the existing repository indexes (`-n`), so refresh the buildroot's indexes
before a new build batch. Results and logs are written to `out/logs`.
No host-system installation or repository signing is performed.

`python3 tools/generate.py` regenerates this repository's recipes. All sources
are checked against their recorded digests by xbps-src. The pinned Glaze 7.2.0
archive is an explicit compositor build source, not a build-time network fallback.

Maintainer: bb8TheRobot <bb8therobot85@gmail.com>.
Packaging code: 0BSD. Upstream licenses and notices remain applicable, including
Abyssparse's LGPL-3.0-only. The upstream attribution audit remains a separate
release prerequisite.
