#!/usr/bin/env python3
"""Compute a new version string from a current version and bump rules.

Usage:
    python bump_version.py CURRENT_VERSION BASE_BUMP STAGE_BUMP

BASE_BUMP: major | minor | patch | stable | (empty)
STAGE_BUMP: alpha | beta | rc | post | dev | (empty)

Prints the resulting PEP 440 version to stdout.
"""
import re
import sys

STAGE_ORDER = {"a": 0, "alpha": 0, "b": 1, "beta": 1, "rc": 2}
STAGE_CANONICAL = {"alpha": "a", "beta": "b", "rc": "rc", "post": "post", "dev": "dev"}

VERSION_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:(?P<pre_kind>a|alpha|b|beta|rc)(?P<pre_num>0|[1-9]\d*))?"
    r"(?:\.post(?P<post>0|[1-9]\d*))?"
    r"(?:\.dev(?P<dev>0|[1-9]\d*))?$"
)


def parse(version: str) -> dict:
    m = VERSION_RE.match(version)
    if not m:
        raise ValueError(f"Invalid version: {version}")
    return {
        "major": int(m.group("major")),
        "minor": int(m.group("minor")),
        "patch": int(m.group("patch")),
        "pre_kind": m.group("pre_kind"),
        "pre_num": int(m.group("pre_num")) if m.group("pre_num") else None,
        "post": int(m.group("post")) if m.group("post") else None,
        "dev": int(m.group("dev")) if m.group("dev") else None,
    }


def format(v: dict) -> str:
    s = f"{v['major']}.{v['minor']}.{v['patch']}"
    if v["pre_kind"] is not None:
        s += f"{STAGE_CANONICAL.get(v['pre_kind'], v['pre_kind'])}{v['pre_num']}"
    if v["post"] is not None:
        s += f".post{v['post']}"
    if v["dev"] is not None:
        s += f".dev{v['dev']}"
    return s


def is_prerelease(v: dict) -> bool:
    return v["pre_kind"] is not None or v["post"] is not None or v["dev"] is not None


def bump(v: dict, base: str, stage: str) -> dict:
    v = dict(v)

    if base == "stable":
        v["pre_kind"] = None
        v["pre_num"] = None
        v["post"] = None
        v["dev"] = None
        return v

    if base in ("major", "minor", "patch"):
        if base == "major":
            v["major"] += 1
            v["minor"] = 0
            v["patch"] = 0
        elif base == "minor":
            v["minor"] += 1
            v["patch"] = 0
        elif base == "patch":
            if is_prerelease(v) and v["pre_kind"] is None:
                pass
            else:
                v["patch"] += 1
        v["pre_kind"] = None
        v["pre_num"] = None
        v["post"] = None
        v["dev"] = None

    if stage:
        canonical = STAGE_CANONICAL.get(stage, stage)
        if canonical in ("a", "b", "rc"):
            if base:
                v["pre_kind"] = canonical
                v["pre_num"] = 1
            else:
                if v["pre_kind"] is not None and STAGE_CANONICAL.get(v["pre_kind"], v["pre_kind"]) == canonical:
                    v["pre_num"] += 1
                else:
                    v["pre_kind"] = canonical
                    v["pre_num"] = 1
        elif canonical == "post":
            if v["post"] is not None and not base:
                v["post"] += 1
            else:
                v["post"] = 1
        elif canonical == "dev":
            if v["dev"] is not None and not base:
                v["dev"] += 1
            else:
                v["dev"] = 1

    return v


def main() -> None:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        sys.exit(2)

    current, base, stage = sys.argv[1], sys.argv[2].strip(), sys.argv[3].strip()

    if not base and not stage:
        print("Error: at least one of base_bump or stage_bump must be set", file=sys.stderr)
        sys.exit(1)
    if base == "stable" and stage:
        print("Error: 'stable' must not be combined with stage_bump", file=sys.stderr)
        sys.exit(1)

    v = parse(current)

    if not base and stage:
        canonical = STAGE_CANONICAL.get(stage, stage)
        if canonical in ("a", "b", "rc") and v["pre_kind"] is None:
            msg = (
                f"Error: stage_bump '{stage}' without base_bump requires "
                f"an existing prerelease version (current: {current})"
            )
            print(msg, file=sys.stderr)
            sys.exit(1)

    new_v = bump(v, base, stage)
    print(format(new_v))


if __name__ == "__main__":
    main()
