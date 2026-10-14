#!/usr/bin/env python3
"""
Archive each release's display config (<module>.display.json) next to its TTL (#140).

An earlier release is published at <site>/<module>/<semver>/<module>.ttl, from versions/<module>/<semver>/. The graph
viewer reads <module>.display.json from the same place, so without the config an earlier release opens with the default
layout and colours. The config is archived with the release and never edited afterwards, like the TTL.

    archive_display_config.py archive <module> <semver> [--ref REF]   # at a release: copy the config at REF (default HEAD)
    archive_display_config.py backfill                                # existing archives that have no config yet

The config comes from git, at the release's tag when there is one (`<module>-v<semver>`), otherwise at the commit that
archived the TTL; a release whose tree has no config at that point takes the current one. stdlib only.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _git(root, *args):
    done = subprocess.run(["git", *args], cwd=root, capture_output=True)
    return done.returncode, done.stdout


def config_at(root, ref, module):
    """The bytes of src/<module>.display.json at git `ref`, or None if it does not exist there."""
    code, out = _git(root, "show", f"{ref}:src/{module}.display.json")
    return out if code == 0 else None


def current_config(root, module):
    path = Path(root) / "src" / f"{module}.display.json"
    return path.read_bytes() if path.is_file() else None


def archive_dir(root, module, version):
    return Path(root) / "versions" / module / version


def archive(root, module, version, ref="HEAD"):
    """Copy the module's config at `ref` to versions/<module>/<version>/. Returns the path, or None if there is none.

    An archived release never changes, so an existing archived config is left alone.
    """
    dest = archive_dir(root, module, version) / f"{module}.display.json"
    if dest.exists():
        return dest
    data = config_at(root, ref, module)
    if data is None:
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest


def release_ref(root, module, version):
    """(ref, how) that names the tree the release was made from: its tag, else the commit that archived its TTL."""
    tag = f"{module}-v{version}"
    if _git(root, "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}^{{commit}}")[0] == 0:
        return f"refs/tags/{tag}", "tag"
    code, out = _git(root, "log", "--diff-filter=A", "--format=%H", "-1", "--", f"versions/{module}/{version}/{module}.ttl")
    sha = out.decode().strip() if code == 0 else ""
    return (sha, "archive commit") if sha else ("HEAD", "current")


def backfill(root=ROOT):
    """Archive the config of every release that has a TTL and no config. Returns [(module, version, how)]."""
    done = []
    versions = Path(root) / "versions"
    if not versions.is_dir():
        return done
    for ttl in sorted(versions.glob("*/*/*.ttl")):
        version, module = ttl.parent.name, ttl.parent.parent.name
        if ttl.stem != module or (ttl.parent / f"{module}.display.json").exists():
            continue
        ref, how = release_ref(root, module, version)
        if archive(root, module, version, ref) is None:
            data = current_config(root, module)
            if data is None:
                continue
            (ttl.parent / f"{module}.display.json").write_bytes(data)
            how = "current"
        done.append((module, version, how))
    return done


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    one = sub.add_parser("archive")
    one.add_argument("module")
    one.add_argument("version")
    one.add_argument("--ref", default="HEAD")
    sub.add_parser("backfill")
    args = ap.parse_args(argv)
    if args.cmd == "archive":
        path = archive(ROOT, args.module, args.version, args.ref)
        print(f"archived {path.relative_to(ROOT).as_posix()}" if path else f"no src/{args.module}.display.json at {args.ref}: nothing to archive")
        return
    for module, version, how in backfill():
        print(f"archived {module} {version} (config from {how})")


if __name__ == "__main__":
    sys.exit(main())
