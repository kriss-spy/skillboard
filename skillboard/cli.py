"""Command-line interface for skillboard.

Provides commands for:
- sync: Interactive skill management with checkbox UI
- list: Show available skills in warehouse
- list-path: Show configured skill paths
- init: Initialize directories
- copy: Copy skills (not symlink)
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import get_config
from .manager import SkillManager
from .tui import run_skill_tui

console = Console()


# Enable -h as well as --help
@click.group(
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
)
@click.version_option(version=__version__, prog_name="skillboard")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Skillboard - A lightweight skill management utility for AI coding agents.

    Manage your AI coding agent skills by toggling them between your warehouse
    and active directories using symbolic links.

    Examples:
        skillboard init                    # Initialize directories
        skillboard list                    # Show available skills
        skillboard list-path               # Show configured paths
        skillboard sync -o claude          # Interactive sync to Claude
        skillboard sync -o agent --no-tui  # Just list skills
    """
    # If no subcommand is provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option(
    "-i",
    "--input",
    "input_path",
    type=str,
    help=(
        "Source directory (warehouse). Can be a path or alias: "
        "warehouse, agent, claude, opencode, gemini, antigravity"
    ),
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=str,
    help=(
        "Target directory (where skills will be linked). Can be a path or alias: "
        "agent, claude, opencode, gemini, antigravity"
    ),
)
@click.option("--no-tui", is_flag=True, help="Run in non-TUI mode (list skills only).")
def sync(input_path: Optional[str], output_path: Optional[str], no_tui: bool) -> None:
    """Sync skills between warehouse and target directory.

    In interactive mode (default), shows a checkbox interface to select
    which skills to enable. In --no-tui mode, just lists current skills.

    \b
    Examples:
        skillboard sync -i warehouse -o claude
        skillboard sync -i ~/.agent/skill-warehouse -o ~/.claude/skills
        skillboard sync -o claude  # Uses warehouse as default source
        skillboard sync -o claude --no-tui
    """
    config = get_config()

    # Resolve input path
    if input_path is None:
        source = config.paths.warehouse
    elif input_path in config.paths.list_paths():
        source = config.paths.get_path(input_path)
    else:
        source = Path(input_path).expanduser()

    # Resolve output path
    if output_path is None:
        console.print("[red]Error: Target directory is required. Use -o/--output option.[/red]")
        console.print("\nAvailable aliases:")
        for name, path in config.paths.list_paths().items():
            if name != "warehouse":
                console.print(f"  {name}: {path}")
        sys.exit(1)
    elif output_path in config.paths.list_paths():
        target = config.paths.get_path(output_path)
    else:
        target = Path(output_path).expanduser()

    # Validate paths
    if not source.exists():
        console.print(f"[red]Error: Source directory does not exist: {source}[/red]")
        sys.exit(1)

    # Create target if it doesn't exist
    target.mkdir(parents=True, exist_ok=True)

    if no_tui:
        # Non-TUI mode: just list skills
        manager = SkillManager(source, target)
        skills = manager.scan_skills()

        if not skills:
            console.print(f"[yellow]No skills found in {source}[/yellow]")
            return

        table = Table(title=f"Skills: {source} → {target}")
        table.add_column("Status", justify="center", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Type", style="yellow")

        for skill in skills:
            status = "✓" if skill.is_enabled else "✗"
            link_type = (
                "symlink" if skill.is_symlink else ("directory" if skill.is_enabled else "-")
            )
            table.add_row(status, skill.name, link_type)

        console.print(table)
        enabled_count = sum(1 for s in skills if s.is_enabled)
        console.print(f"\n[dim]Total: {len(skills)} skills, {enabled_count} enabled[/dim]")
    else:
        # Interactive TUI mode
        run_skill_tui(source, target)


@cli.command("list-path")
def list_path() -> None:
    """List all configured skill paths.

    Shows all the skill directories that skillboard knows about,
    along with whether they exist.
    """
    config = get_config()

    table = Table(title="Configured Skill Paths")
    table.add_column("Alias", style="cyan", no_wrap=True)
    table.add_column("Path", style="green")
    table.add_column("Exists", justify="center")

    for name, path in config.paths.list_paths().items():
        exists = "✓" if path.exists() else "✗"
        exists_style = "green" if path.exists() else "red"
        table.add_row(name, str(path), f"[{exists_style}]{exists}[/{exists_style}]")

    console.print(table)

    # Show config file location
    console.print(f"\n[dim]Config file: {config.CONFIG_FILE}[/dim]")


@cli.command()
@click.argument("agent", required=False)
def list(agent: Optional[str]) -> None:
    """List available skills.

    Shows skills from both global and local locations.

    \b
    Examples:
        skillboard list           # Show all .agent skills (global + local)
        skillboard list claude    # Show Claude skills (~/.claude/skills + ./claude/skills)
        skillboard list agent     # Show agent skills (~/.agent/skills + ./agent/skills)
        skillboard list gemini    # Show Gemini skills (~/.gemini/skills + ./gemini/skills)
    """
    config = get_config()

    if agent is None:
        # Default: show .agent skills (warehouse + local)
        _list_skills_from_locations("Agent Skills", config.paths.agent, Path(".agent/skills"))
    else:
        # Show skills for specific agent
        agent_lower = agent.lower()
        if agent_lower in config.paths.list_paths():
            agent_path = config.paths.get_path(agent_lower)
            local_path = Path(f"./{agent_lower}/skills")
            _list_skills_from_locations(f"{agent.capitalize()} Skills", agent_path, local_path)
        else:
            console.print(f"[red]Unknown agent: {agent}[/red]")
            console.print(f"Available: {', '.join(config.paths.list_paths().keys())}")


def _list_skills_from_locations(title: str, global_path: Path, local_path: Path) -> None:
    """Helper to list skills from global and local paths."""
    console.print(f"\n[bold]{title}:[/bold]")

    total_skills = 0

    # Global skills
    if global_path.exists():
        manager = SkillManager(global_path, global_path)
        skills = manager.get_source_skills()
        if skills:
            console.print(f"\n  [cyan]Global ({global_path}):[/cyan]")
            for skill in skills:
                console.print(f"    ✓ {skill.name}")
            total_skills += len(skills)
        else:
            console.print(f"\n  [dim]Global ({global_path}): None[/dim]")
    else:
        console.print(f"\n  [dim]Global ({global_path}): Not initialized[/dim]")

    # Local skills
    if local_path.exists() and local_path.is_dir():
        manager = SkillManager(local_path, local_path)
        skills = manager.get_source_skills()
        if skills:
            console.print(f"\n  [cyan]Local ({local_path}):[/cyan]")
            for skill in skills:
                console.print(f"    ✓ {skill.name}")
            total_skills += len(skills)
        else:
            console.print(f"\n  [dim]Local ({local_path}): None[/dim]")
    else:
        console.print(f"\n  [dim]Local ({local_path}): Not found[/dim]")

    console.print(f"\n[dim]Total: {total_skills} skills[/dim]")
    console.print()


@cli.command()
def init() -> None:
    """Initialize skillboard configuration and directories.

    Creates the warehouse directory and any missing agent directories.
    Also saves the configuration file.
    """
    config = get_config()

    console.print("[bold]Initializing skillboard...[/bold]\n")

    paths_created = []
    for name, path in config.paths.list_paths().items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            paths_created.append((name, path))
            console.print(f"[green]✓ Created:[/green] {name} → {path}")
        else:
            console.print(f"[dim]✓ Exists:[/dim] {name} → {path}")

    # Save config
    config.save_config()

    console.print(f"\n[bold]Configuration saved to:[/bold] {config.CONFIG_FILE}")

    if paths_created:
        console.print(f"\n[green]Created {len(paths_created)} new directories.[/green]")
    else:
        console.print("\n[dim]All directories already exist.[/dim]")


@cli.command()
@click.argument("source")
@click.argument("target")
def copy(source: str, target: str) -> None:
    """Copy skills from source to target (not symlink).

    Unlike sync, this creates actual copies of the skill directories
    instead of symbolic links.

    \b
    Example:
        skillboard copy warehouse claude
        skillboard copy ~/.agent/skills ~/.claude/skills
    """
    config = get_config()

    # Resolve paths
    if source in config.paths.list_paths():
        source_path = config.paths.get_path(source)
    else:
        source_path = Path(source).expanduser()

    if target in config.paths.list_paths():
        target_path = config.paths.get_path(target)
    else:
        target_path = Path(target).expanduser()

    if not source_path.exists():
        console.print(f"[red]Error: Source does not exist: {source_path}[/red]")
        sys.exit(1)

    target_path.mkdir(parents=True, exist_ok=True)

    manager = SkillManager(source_path, target_path)
    skills = manager.get_source_skills()

    if not skills:
        console.print(f"[yellow]No skills found in {source_path}[/yellow]")
        return

    console.print(f"Copying {len(skills)} skills from {source_path} to {target_path}...\n")

    import shutil

    copied = 0
    skipped = 0
    errors = 0

    for skill in skills:
        dest = target_path / skill.name
        if dest.exists():
            console.print(f"[yellow]⚠ Skipped (exists):[/yellow] {skill.name}")
            skipped += 1
        else:
            try:
                shutil.copytree(skill.path, dest)
                console.print(f"[green]✓ Copied:[/green] {skill.name}")
                copied += 1
            except Exception as e:
                console.print(f"[red]✗ Error copying {skill.name}: {e}[/red]")
                errors += 1

    console.print(f"\n[bold]Results:[/bold] {copied} copied, {skipped} skipped, {errors} errors")


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
