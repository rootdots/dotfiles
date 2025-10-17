#!/usr/bin/env python3.11
import subprocess
import sys
import re
from pathlib import Path


def run(cmd: str, capture_output: bool = False) -> str | None:
    result: subprocess.CompletedProcess[str] = subprocess.run(
        cmd,
        shell=True,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture_output else None,
    )
    return result.stdout.strip() if capture_output else None


def bump_version(manual_type: str | None = None) -> str:
    current: str = run(cmd="git-cliff --bumped-version", capture_output=True) or "0.0.0"
    major, minor, patch = map(int, current.split(sep="."))

    match manual_type:
        case "major":
            major += 1
            minor = 0
            patch = 0
        case "minor":
            minor += 1
            patch = 0
        case "patch":
            patch += 1
        case None:
            return current
        case _:
            print("❌ Invalid bump type. Use: major, minor, patch or leave empty.")
            sys.exit(1)

    return f"{major}.{minor}.{patch}"


def update_version_file(new_version: str) -> None:
    pyproject: Path = Path("pyproject.toml")
    if pyproject.exists():
        content: str = pyproject.read_text()
        updated: str = re.sub(
            r'version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"',
            f'version = "{new_version}"',
            content,
        )
        _ = pyproject.write_text(data=updated)
        _ = run(cmd="git add pyproject.toml")
    else:
        _ = Path("VERSION").write_text(data=new_version + "\n")
        _ = run(cmd="git add VERSION")


def main() -> None:
    bump_type: str | None = sys.argv[1] if len(sys.argv) > 1 else None
    new_version: str = bump_version(manual_type=bump_type)
    print(f"🔢 New version: {new_version}")

    update_version_file(new_version)

    _ = run(cmd=f'git commit -m "chore: release v{new_version}"')
    _ = run(cmd=f"git tag v{new_version}")
    _ = run(cmd=f"git-cliff -t v{new_version} -o CHANGELOG.md")
    _ = run(cmd="git add CHANGELOG.md")
    _ = run(cmd=f'git commit -m "docs: update changelog for v{new_version}"')
    _ = run(cmd="git push")
    _ = run(cmd=f"git push origin v{new_version}")

    print(f"✅ Release v{new_version} complete!")


if __name__ == "__main__":
    main()
