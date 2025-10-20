import subprocess
import re
from pathlib import Path
import typer

app = typer.Typer()


def run(
    cmd: list[str], capture_output: bool = False, dry_run: bool = False
) -> str | None:
    cmd_str = " ".join(cmd)
    if dry_run:
        typer.echo(f"[dry-run] Would run: {cmd_str}")
        return ""
    result = subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture_output else None,
    )
    return result.stdout.strip() if capture_output else None


def normalize_version(version: str) -> str:
    return version.lstrip("v")


def is_valid_semver(version: str) -> bool:
    return re.match(r"^v?[0-9]+\.[0-9]+\.[0-9]+$", version) is not None


def get_current_version(dry_run: bool = False) -> str:
    version = (
        run(["git-cliff", "--bumped-version"], capture_output=True, dry_run=dry_run)
        or "0.0.0"
    )
    version = normalize_version(version)
    if not is_valid_semver(version):
        typer.echo(f"❌ Invalid version format: {version}")
        raise typer.Exit(code=1)
    return version


def bump_version(current: str, bump_type: str | None) -> str:
    major, minor, patch = map(int, current.split("."))
    match bump_type:
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
            typer.echo("❌ Invalid bump type. Use: major, minor, patch or leave empty.")
            raise typer.Exit(code=1)
    return f"{major}.{minor}.{patch}"


def update_pyproject_version(new_version: str, dry_run: bool = False) -> None:
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        typer.echo("⚠️ pyproject.toml not found. Skipping version update.")
        return

    content = pyproject.read_text()
    updated = re.sub(
        r'version\s*=\s*"v?[0-9]+\.[0-9]+\.[0-9]+"',
        f'version = "{new_version}"',
        content,
    )
    if dry_run:
        typer.echo(f"[dry-run] Would update pyproject.toml to version: {new_version}")
    else:
        pyproject.write_text(updated)
        run(["git", "add", "pyproject.toml"])


@app.command()
def release(
    bump: str | None = typer.Argument(
        None, help="Version bump type: major, minor, patch or leave empty"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Simulate the release process"
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
) -> None:
    current = get_current_version(dry_run=dry_run)
    new_version = bump_version(current, bump)
    tag_version = f"v{new_version}"

    typer.echo(f"🔢 Current version: {current}")
    typer.echo(f"🚀 New version: {new_version}")

    if not dry_run and not typer.confirm(f"Proceed with release {tag_version}?"):
        typer.echo("❌ Release aborted.")
        raise typer.Exit()

    update_pyproject_version(new_version, dry_run=dry_run)

    run(["git", "commit", "-m", f"chore: release {tag_version}"], dry_run=dry_run)
    run(["git", "tag", tag_version], dry_run=dry_run)
    run(["git-cliff", "-t", tag_version, "-o", "CHANGELOG.md"], dry_run=dry_run)
    run(["git", "add", "CHANGELOG.md"], dry_run=dry_run)
    run(
        ["git", "commit", "-m", f"docs: update changelog for {tag_version}"],
        dry_run=dry_run,
    )
    run(["git", "push"], dry_run=dry_run)
    run(["git", "push", "origin", tag_version], dry_run=dry_run)

    typer.echo(f"✅ Release {tag_version} complete{' (simulated)' if dry_run else ''}!")


if __name__ == "__main__":
    app()
