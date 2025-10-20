import subprocess
import re
from pathlib import Path
import typer

app = typer.Typer()


def run(cmd: str, capture_output: bool = False, dry_run: bool = False) -> str | None:
    if dry_run:
        typer.echo(f"[dry-run] Would run: {cmd}")
        return ""
    result = subprocess.run(
        cmd,
        shell=True,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture_output else None,
    )
    return result.stdout.strip() if capture_output else None


def bump_version(manual_type: str | None = None, dry_run: bool = False) -> str:
    current = (
        run("git-cliff --bumped-version", capture_output=True, dry_run=dry_run)
        or "0.0.0"
    )
    major, minor, patch = map(int, current.split("."))

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
            typer.echo(
                "❌ Invalid version type. Use: major, minor, patch or leave empty."
            )
            raise typer.Exit(code=1)

    return f"{major}.{minor}.{patch}"


def update_version_file(new_version: str, dry_run: bool = False) -> None:
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        content = pyproject.read_text()
        updated = re.sub(
            r'version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"',
            f'version = "{new_version}"',
            content,
        )
        if dry_run:
            typer.echo(
                f"[dry-run] Would update pyproject.toml with version: {new_version}"
            )
        else:
            _ = pyproject.write_text(updated)
            _ = run("git add pyproject.toml")
    else:
        if dry_run:
            typer.echo(f"[dry-run] Would write VERSION file with: {new_version}")
        else:
            _ = Path("VERSION").write_text(new_version + "\n")
            _ = run("git add VERSION")


@app.command()
def release(
    bump: str | None = typer.Argument(
        None, help="Version bump type: major, minor, patch or leave empty for auto"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Simulate the release process without making changes"
    ),
) -> None:
    new_version = bump_version(bump, dry_run=dry_run)
    typer.echo(f"🔢 New version: {new_version}")

    update_version_file(new_version, dry_run=dry_run)

    _ = run(f'git commit -m "chore: release v{new_version}"', dry_run=dry_run)
    _ = run(f"git tag v{new_version}", dry_run=dry_run)
    _ = run(f"git-cliff -t v{new_version} -o CHANGELOG.md", dry_run=dry_run)
    _ = run("git add CHANGELOG.md", dry_run=dry_run)
    _ = run(
        f'git commit -m "docs: update changelog for v{new_version}"', dry_run=dry_run
    )
    _ = run("git push", dry_run=dry_run)
    _ = run(f"git push origin v{new_version}", dry_run=dry_run)

    typer.echo(
        f"✅ Release v{new_version} complete{' (simulated)' if dry_run else ''}!"
    )


if __name__ == "__main__":
    app()
