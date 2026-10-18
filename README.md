<div align="center">

<img src="https://github.com/AbyssWM.png?size=200" width="140" alt="AbyssWM logo">

# 🌊 Abyss for Void Linux

**xbps-src templates for the Abyss Wayland ecosystem (17 packages)**

![Void](https://img.shields.io/badge/Void-xbps--src-478061?logo=voidlinux&logoColor=white) ![Arch](https://img.shields.io/badge/x86__64-glibc-informational) ![Native build](https://img.shields.io/badge/native%20build-17%2F17%20passed-brightgreen) ![Install tests](https://img.shields.io/badge/install%20%2F%20session%20tests-pending-lightgrey) ![License](https://img.shields.io/badge/recipes-0BSD-blue)

[Website](https://abysswm.github.io) · [Getting started](https://abysswm.github.io/wiki/getting-started) · [Organization](https://github.com/AbyssWM)

</div>

---

Third-party development templates, not part of Void's official repository. Packages are built locally with `xbps-src`; no binary repository is hosted yet. The seven libraries also produce `-devel` subpackages, and `shlibs` supplies their SONAME mappings.

## 🚀 Installation

### Prebuilt packages (recommended)

```sh
echo "repository=https://abysswm.github.io/void" | sudo tee /etc/xbps.d/abyss.conf
sudo xbps-install -S abyssland
```

Signed binary repository: [AbyssWM/void](https://github.com/AbyssWM/void). On the first sync xbps asks to import the key of `bb8TheRobot <bb8therobot85@gmail.com>` — answer **y**.

### Build it yourself

**1. Get the official build system** and bootstrap it as an ordinary user:

```sh
git clone https://github.com/void-linux/void-packages.git
git clone https://github.com/AbyssWM/void-builds.git
```

**2. Copy the templates and shlibs entries.** `tools/prepare.py` copies every template in `srcpkgs/` (including the `-devel` symlinks) and merges the `shlibs` lines into `common/shlibs`. It refuses to overwrite unrelated templates:

```sh
python3 void-builds/tools/prepare.py void-packages
```

**3. Bootstrap and build:**

```sh
cd void-packages
./xbps-src binary-bootstrap
./xbps-src pkg abyssland
```

Dependencies from this overlay (`abyssutils`, `abysswire`, ...) are built automatically from their templates. For the bubblewrap setup used by the maintainer, set `XBPS_CHROOT_CMD=bwrap` in `etc/conf`.

**4. Install from the local repository:**

```sh
sudo xbps-install -R hostdir/binpkgs abyssland
```

Then continue with the [getting-started guide](https://abysswm.github.io/wiki/getting-started).

## 📦 Packages

| Package | Category | Version | Description |
|---|---|---|---|
| `abyssutils` | Library | 0.14.2 | Utility library for the Abyss ecosystem |
| `abyss-scanner` | Tool | 0.4.5 | C++ Wayland protocol scanner for Abyss |
| `abyssland-protocols` | Library | 0.7.0 | Wayland protocol extensions for Abyss |
| `abyssparse` | Library | 0.6.8 | Configuration parsing library for Abyss |
| `abysswire` | Library | 0.3.1 | IPC wire protocol library and scanner for Abyss |
| `abyssgraphics` | Library | 0.5.1 | Graphics and resource library for Abyss |
| `abyssal` | Library | 0.15.0 | Rendering and display backend library for Abyss |
| `abysstoolkit` | Library | 0.6.0 | Native graphical toolkit and config preprocessor for Abyss |
| `abysscursor` | Library | 0.1.13 | Cursor library and theme tools for Abyss |
| `abyssland` | Compositor | 0.56.2 | Dynamic tiling Wayland compositor with C++ configuration |
| `abyss-guiutils` | Application | 0.2.2 | Dialogs and application tools for Abyss |
| `xdg-desktop-portal-abyss` | Desktop integration | 1.4.1 | Desktop portal and screen sharing picker for Abyss |
| `abysspicker` | Application | 0.4.7 | Wayland color picker for Abyss |
| `abyssdusk` | Application | 0.4.0 | Display color temperature manager for Abyss |
| `abysspaper` | Application | 0.8.4 | Wallpaper manager for Abyss |
| `abysslock` | Application | 0.9.6 | Wayland session lock for Abyss |
| `abysspolkit` | Application | 0.2.0 | Polkit authentication agent for Abyss |

Libraries (`abyssutils`, `abyssparse`, `abysswire`, `abyssgraphics`, `abyssal`, `abysstoolkit`, `abysscursor`) additionally ship `-devel` packages. The compositor compiles the public default config, never the packager's personal configuration; the pinned Glaze 7.2.0 archive is an explicit build source, not a network fallback.

## ✅ Status

Honest state as of 2026-10-17/18:

- **Built natively:** all 17 primary packages built with official `xbps-src` on x86_64/glibc in an isolated buildroot. Exact artifact hashes: `BUILD-RESULTS.json`. `abyssparse-0.6.8.20261017_2` (license revision) was rebuilt and its `LICENSE`, `COPYING` and `COPYRIGHT` verified byte-for-byte in the package. A smoke build of `abyssland-protocols` was repeated on 2026-10-18 from the current templates and succeeded; templates match `sources.json` commits and hashes.
- **Not tested:** installation on a real system, live desktop/session, authentication, other architectures, musl, signing, public binary hosting. Project test suites were disabled for the packaging build.
- The upstream attribution audit remains a separate release prerequisite.

## 🛠️ Maintainer tools

<details>
<summary>Regeneration, driver and checks</summary>

`sources.json` pins the public archives and their hashes; `catalog.json` records dependencies and package names. All sources are checked against their digests by xbps-src.

`python3 tools/generate.py` regenerates the recipes. To build all packages in dependency order (stops on the first failure, uses existing indexes via `-n`, so refresh the buildroot's indexes before a new batch):

```sh
python3 tools/build.py /path/to/void-packages --logs out/logs --jobs 2
```

No host installation or repository signing is performed.

</details>

## 📄 License

Maintainer: bb8TheRobot <bb8therobot85@gmail.com>. Packaging code: 0BSD. Upstream licenses and notices remain applicable, including Abyssparse's LGPL-3.0-only. See [LICENSES.md](LICENSES.md).
