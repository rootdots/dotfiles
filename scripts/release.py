import re
import subprocess
from pathlib import Path
from typing import Annotated, TypedDict
import tomllib
import typer

app = typer.Typer(add_completion=False)


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

    # Läs-kommandon (som inte förändrar något i git/filsystem) tillåts köra under dry-run
    is_read_only = capture_output or (
        len(cmd) > 1 and cmd[0] == "git-cliff" and "--bumped-version" in cmd
    )

    if dry_run or verbose:
        prefix = "[dry-run]" if dry_run else "[verbose]"
        typer.echo(f"{prefix} Running: {cmd_str}")

    # Om det är dry-run OCH kommandot förändrar tillstånd, hoppa över exekvering
    if dry_run and not is_read_only:
        return None

    try:
        result = subprocess.run(
            cmd,
            check=True,
            text=True,
            stdout=subprocess.PIPE if capture_output else None,
            stderr=subprocess.PIPE if capture_output else None,
        )
        return result.stdout.strip() if capture_output and result.stdout else None
    except subprocess.CalledProcessError as e:
        stderr_msg = f": {e.stderr.strip()}" if e.stderr else ""
        typer.echo(f"❌ Command failed execution '{cmd_str}'{stderr_msg}")
        raise typer.Exit(code=1) from e
    except FileNotFoundError:
        typer.echo(f"❌ Command not found: '{cmd[0]}'. Make sure it is installed.")
        raise typer.Exit(code=1)


def normalize_version(version: str) -> str:
    return version.lstrip("v").strip()


def is_valid_semver(version: str) -> bool:
    return re.match(r"^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$", version) is not None


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
    try:
        base_version = current.split("-")[0]
        major, minor, patch = map(int, base_version.split("."))
    except ValueError:
        typer.echo(
            f"❌ Cannot parse current version '{current}' into major.minor.patch format."
        )
        raise typer.Exit(code=1)

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

    content = pyproject.read_text(encoding="utf-8")

    # Regex som söker enbart under [project]-sektionen
    pattern = r'(?m)(^\[project\][\s\S]*?^version\s*=\s*")[^"]+(")'
    if not re.search(pattern, content):
        typer.echo(
            "⚠️ Could not find a valid 'version' field under [project] in pyproject.toml"
        )
        return

    updated = re.sub(pattern, rf"\g<1>{new_version}\g<2>", content, count=1)

    if dry_run:
        typer.echo(f"[dry-run] Would update pyproject.toml to version: {new_version}")
    else:
        pyproject.write_text(updated, encoding="utf-8")


@app.command()
def release(
    bump: Annotated[
        str | None,
        typer.Argument(help="Version bump type: major, minor, patch or leave empty"),
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Simulate the release process")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", help="Enable verbose output")
    ] = False,
    preview_changelog: Annotated[
        bool,
        typer.Option(
            "--preview-changelog", help="Preview full changelog before committing"
        ),
    ] = False,
    publish_github: Annotated[
        bool, typer.Option("--publish-github", help="Publish release to GitHub")
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
        detected = run(
            ["git-cliff", "--bumped-version"],
            capture_output=True,
            dry_run=dry_run,
            verbose=verbose,
        )
        if detected:
            new_version = normalize_version(detected)
        else:
            if verbose:
                typer.echo(
                    "[verbose] git-cliff found no bump, defaulting to patch bump."
                )
            new_version = bump_version(current, "patch", verbose=verbose)
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
            typer.echo("\n📜 Full Changelog Preview:\n")
            typer.echo(preview)
            typer.echo("\n📜 End of Preview\n")

    if not dry_run and not typer.confirm(f"Proceed with release {tag_version}?"):
        typer.echo("❌ Release aborted.")
        raise typer.Exit()

    # 1. Uppdatera pyproject.toml
    update_pyproject_version(new_version, dry_run=dry_run, verbose=verbose)

    # 2. Generera changelog för den nya taggen
    run(
        ["git-cliff", "-t", tag_version, "-o", "CHANGELOG.md"],
        dry_run=dry_run,
        verbose=verbose,
    )

    # 3. Stega alla ändrade filer (pyproject.toml + CHANGELOG.md) och göra EN samlad commit
    run(
        ["git", "add", "pyproject.toml", "CHANGELOG.md"],
        dry_run=dry_run,
        verbose=verbose,
    )
    run(
        ["git", "commit", "-m", f"chore(release): prepare {tag_version}"],
        dry_run=dry_run,
        verbose=verbose,
    )

    # 4. Taggning och Push
    run(["git", "tag", tag_version], dry_run=dry_run, verbose=verbose)
    run(["git", "push"], dry_run=dry_run, verbose=verbose)
    run(["git", "push", "origin", tag_version], dry_run=dry_run, verbose=verbose)

    # 5. Publicera på GitHub
    if publish_github:
        run(
            ["gh", "release", "create", tag_version, "--notes-file", "CHANGELOG.md"],
            dry_run=dry_run,
            verbose=verbose,
        )
        typer.echo(f"🚀 Published release {tag_version} to GitHub")

    typer.echo(f"✅ Release {tag_version} complete{' (simulated)' if dry_run else ''}!")


if __name__ == "__main__":
    app()
