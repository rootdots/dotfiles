import subprocess
import re
from pathlib import Path
import typer
import tomllib
from typing import Annotated, TypedDict

app = typer.Typer()


class ProjectMetadata(TypedDict, total=False):
    version: str


class PyprojectData(TypedDict, total=False):
    project: ProjectMetadata


def run(
    cmd: list[str],
    capture_output: bool = False,
    dry_run: bool = False,
    verbose: bool = False,
) -> str | None:
    cmd_str = " ".join(cmd)
    if dry_run or verbose:
        typer.echo(f"{'[dry-run]' if dry_run else '[verbose]'} Running: {cmd_str}")
    if dry_run:
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


def get_current_version(dry_run: bool = False, verbose: bool = False) -> str:
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        try:
            with pyproject.open("rb") as f:
                raw_data = tomllib.load(f)

            if (
                "project" in raw_data
                and isinstance(raw_data["project"], dict)
                and "version" in raw_data["project"]
                and isinstance(raw_data["project"]["version"], str)
            ):
                version = raw_data["project"]["version"]
                if verbose:
                    typer.echo(f"[verbose] Found version in pyproject.toml: {version}")
                return normalize_version(version)
        except Exception as e:
            typer.echo(f"⚠️ Failed to read pyproject.toml: {e}")
    version = (
        run(
            ["git-cliff", "--bumped-version"],
            capture_output=True,
            dry_run=dry_run,
            verbose=verbose,
        )
        or "0.0.0"
    )
    version = normalize_version(version)
    if not is_valid_semver(version):
        typer.echo(f"❌ Invalid version format: {version}")
        raise typer.Exit(code=1)
    return version


def bump_version(current: str, bump_type: str | None, verbose: bool = False) -> str:
    major, minor, patch = map(int, current.split("."))
    if verbose:
        typer.echo(
            f"[verbose] Current version parts: major={major}, minor={minor}, patch={patch}"
        )
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
    new_version = f"{major}.{minor}.{patch}"
    if verbose:
        typer.echo(f"[verbose] Bumped version: {new_version}")
    return new_version


def update_pyproject_version(
    new_version: str, dry_run: bool = False, verbose: bool = False
) -> None:
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
        _ = pyproject.write_text(updated)
        _ = run(["git", "add", "pyproject.toml"], dry_run=dry_run, verbose=verbose)


@app.command()
def release(
    bump: Annotated[
        str | None,
        typer.Argument(help="Version bump type: major, minor, patch or leave empty"),
    ] = None,
    dry_run: Annotated[bool, typer.Option(help="Simulate the release process")] = False,
    verbose: Annotated[bool, typer.Option(help="Enable verbose output")] = False,
    preview_changelog: Annotated[
        bool, typer.Option(help="Preview changelog before committing")
    ] = False,
) -> None:
    if verbose:
        typer.echo("📣 Verbose mode enabled")
        typer.echo(f"[verbose] Bump type: {bump}")
        typer.echo(
            f"[verbose] pyproject.toml exists: {Path('pyproject.toml').exists()}"
        )

    current = get_current_version(dry_run=dry_run, verbose=verbose)

    if bump is None:
        new_version = (
            run(
                ["git-cliff", "--bumped-version"],
                capture_output=True,
                dry_run=dry_run,
                verbose=verbose,
            )
            or current
        )
        new_version = normalize_version(new_version)
        if verbose:
            typer.echo(
                f"[verbose] Auto-detected version bump from git-cliff: {new_version}"
            )
    else:
        new_version = bump_version(current, bump, verbose=verbose)

    tag_version = f"v{new_version}"

    typer.echo(f"🔢 Current version: {current}")
    typer.echo(f"🚀 New version: {new_version}")

    if preview_changelog:
        preview = run(
            ["git-cliff", "--unreleased"],
            capture_output=True,
            dry_run=dry_run,
            verbose=verbose,
        )
        if preview:
            typer.echo("\n📜 Changelog Preview:\n")
            typer.echo(preview)
            typer.echo("\n📜 End of Preview\n")

    if not dry_run and not typer.confirm(f"Proceed with release {tag_version}?"):
        typer.echo("❌ Release aborted.")
        raise typer.Exit()

    update_pyproject_version(new_version, dry_run=dry_run, verbose=verbose)

    _ = run(
        ["git", "commit", "-m", f"chore: release {tag_version}"],
        dry_run=dry_run,
        verbose=verbose,
    )

    _ = run(
        ["git-cliff", "--unreleased", "-o", "CHANGELOG.md"],
        dry_run=dry_run,
        verbose=verbose,
    )

    _ = run(["git", "add", "CHANGELOG.md"], dry_run=dry_run, verbose=verbose)
    _ = run(
        ["git", "commit", "-m", f"docs: update changelog for {tag_version}"],
        dry_run=dry_run,
        verbose=verbose,
    )
    _ = run(["git", "tag", tag_version], dry_run=dry_run, verbose=verbose)
    _ = run(["git", "push"], dry_run=dry_run, verbose=verbose)
    _ = run(["git", "push", "origin", tag_version], dry_run=dry_run, verbose=verbose)

    typer.echo(f"✅ Release {tag_version} complete{' (simulated)' if dry_run else ''}!")


if __name__ == "__main__":
    app()
