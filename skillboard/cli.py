"""Command-line interface for skillboard.

Provides commands for:
- sync: Interactive skill management with checkbox UI
- list: Show available skills in warehouse
- list-path: Show configured skill paths
- init: Initialize directories
- copy: Copy skills (not symlink)
- move: Move skills between locations
"""

import shutil
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import get_config
from .manager import SkillManager, are_skills_identical
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
    help="Source agent (claude, agent, gemini, opencode, antigravity, warehouse).",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=str,
    help="Target agent (claude, agent, gemini, opencode, antigravity).",
)
@click.option(
    "--input-scope",
    type=click.Choice(["global", "local"], case_sensitive=False),
    default="global",
    help="Scope for input: global (~/.<agent>/skills) or local (./.<agent>/skills).",
)
@click.option(
    "--output-scope",
    type=click.Choice(["global", "local"], case_sensitive=False),
    default="global",
    help="Scope for output: global (~/.<agent>/skills) or local (./.<agent>/skills).",
)
@click.option(
    "--all",
    "sync_all",
    is_flag=True,
    help="Sync from both global and local sources.",
)
@click.option(
    "--verbose",
    "verbose_mode",
    is_flag=True,
    help="Show full table of skills (default: summary only).",
)
@click.option("--no-tui", is_flag=True, help="Run in non-TUI mode (list skills only).")
def sync(
    input_path: Optional[str],
    output_path: Optional[str],
    input_scope: str,
    output_scope: str,
    sync_all: bool,
    verbose_mode: bool,
    no_tui: bool,
) -> None:
    """Sync skills between source and target directories.

    \b
    Examples:
        skillboard sync -o claude                    # global -> global
        skillboard sync -i claude -o agent           # global claude -> global agent
        skillboard sync -i claude --input-scope local -o agent   # local claude -> global agent
        skillboard sync -i claude -o agent --output-scope local  # global claude -> local agent
        skillboard sync -i claude --all -o agent     # (global+local) claude -> global agent
    """
    config = get_config()

    # Resolve source
    if input_path is None:
        # Default source is agent
        source_agent = "agent"
    else:
        source_agent = input_path.lower()

    if sync_all:
        # Need to handle multiple sources
        sources = []
        if source_agent in config.paths.list_paths():
            global_path = config.paths.get_path(source_agent)
            if global_path.exists():
                sources.append(global_path)
            local_path = Path(f"./.{source_agent}/skills")
            if local_path.exists():
                sources.append(local_path)
        else:
            console.print(f"[red]Unknown source agent: {source_agent}[/red]")
            sys.exit(1)

        if not sources:
            console.print(f"[red]No skills found for {source_agent}[/red]")
            sys.exit(1)

        # For now, use first available source
        source = sources[0]
        if len(sources) > 1:
            console.print(f"[dim]Note: Using {sources[0]} (found {len(sources)} sources)[/dim]")
    else:
        # Single source based on scope
        if source_agent in config.paths.list_paths():
            if input_scope == "local":
                source = Path(f"./.{source_agent}/skills")
            else:
                source = config.paths.get_path(source_agent)
        else:
            console.print(f"[red]Unknown source agent: {source_agent}[/red]")
            console.print(f"Available: {', '.join(config.paths.list_paths().keys())}")
            sys.exit(1)

    # Resolve target
    if output_path is None:
        console.print("[red]Error: Target directory is required. Use -o/--output option.[/red]")
        sys.exit(1)

    target_agent = output_path.lower()
    if target_agent in config.paths.list_paths():
        if output_scope == "local":
            target = Path(f"./.{target_agent}/skills")
        else:
            target = config.paths.get_path(target_agent)
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

        enabled_count = sum(1 for s in skills if s.is_enabled)
        available_count = len(skills) - enabled_count

        if verbose_mode:
            # Show full table
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
        else:
            # Show compact summary
            console.print(f"\n[bold]Sync Summary:[/bold] {source} → {target}")
            console.print(f"  Total:     {len(skills)} skills")
            console.print(f"  Enabled:   {enabled_count} skills")
            console.print(f"  Available: {available_count} skills")

        console.print("\n[dim]Use --verbose to see full skill list[/dim]")
    else:
        # Interactive TUI mode
        run_skill_tui(source, target)


@cli.command("list-path")
def list_path() -> None:
    """List all configured skill paths with skill counts.

    Shows all the skill directories that skillboard knows about,
    along with whether they exist and how many skills they contain.
    """
    from skillboard.manager import count_skills_in_directory

    config = get_config()

    table = Table(title="Configured Skill Paths")
    table.add_column("Alias", style="cyan", no_wrap=True)
    table.add_column("Path", style="green")
    table.add_column("Exists", justify="center")
    table.add_column("Skills", justify="right", style="yellow")

    for name, path in config.paths.list_paths().items():
        exists = "✓" if path.exists() else "✗"
        exists_style = "green" if path.exists() else "red"
        skill_count = count_skills_in_directory(path)
        count_str = str(skill_count) if path.exists() else "-"
        table.add_row(
            name,
            str(path),
            f"[{exists_style}]{exists}[/{exists_style}]",
            count_str,
        )

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
            local_path = Path(f"./.{agent_lower}/skills")
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
@click.option(
    "-i",
    "--input",
    "input_path",
    type=str,
    help="Source agent (claude, agent, gemini, opencode, antigravity, warehouse).",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=str,
    help="Target agent (claude, agent, gemini, opencode, antigravity).",
)
@click.option(
    "--input-scope",
    type=click.Choice(["global", "local"], case_sensitive=False),
    default="global",
    help="Scope for input: global (~/.<agent>/skills) or local (./.<agent>/skills).",
)
@click.option(
    "--output-scope",
    type=click.Choice(["global", "local"], case_sensitive=False),
    default="global",
    help="Scope for output: global (~/.<agent>/skills) or local (./.<agent>/skills).",
)
def copy(
    input_path: Optional[str],
    output_path: Optional[str],
    input_scope: str,
    output_scope: str,
) -> None:
    """Copy skills from source to target (not symlink).

    Unlike sync, this creates actual copies of the skill directories.

    \b
    Examples:
        skillboard copy -i claude -o agent                    # global -> global
        skillboard copy -i claude --input-scope local -o agent # local -> global
        skillboard copy -i claude -o agent --output-scope local # global -> local
    """
    config = get_config()

    # Resolve source
    if input_path is None:
        console.print("[red]Error: Source is required. Use -i/--input option.[/red]")
        sys.exit(1)

    source_agent = input_path.lower()
    if source_agent in config.paths.list_paths():
        if input_scope == "local":
            source_path = Path(f"./.{source_agent}/skills")
        else:
            source_path = config.paths.get_path(source_agent)
    else:
        source_path = Path(input_path).expanduser()

    # Resolve target
    if output_path is None:
        console.print("[red]Error: Target is required. Use -o/--output option.[/red]")
        sys.exit(1)

    target_agent = output_path.lower()
    if target_agent in config.paths.list_paths():
        if output_scope == "local":
            target_path = Path(f"./.{target_agent}/skills")
        else:
            target_path = config.paths.get_path(target_agent)
    else:
        target_path = Path(output_path).expanduser()

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


@cli.command()
@click.option(
    "-i",
    "--input",
    "input_path",
    type=str,
    help="Source agent (claude, agent, gemini, opencode, antigravity, warehouse).",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=str,
    help="Target agent (claude, agent, gemini, opencode, antigravity).",
)
@click.option(
    "--input-scope",
    type=click.Choice(["global", "local"], case_sensitive=False),
    default="global",
    help="Scope for input: global (~/.<agent>/skills) or local (./.<agent>/skills).",
)
@click.option(
    "--output-scope",
    type=click.Choice(["global", "local"], case_sensitive=False),
    default="global",
    help="Scope for output: global (~/.<agent>/skills) or local (./.<agent>/skills).",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing skills in target without prompting.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be moved without actually moving.",
)
def move(
    input_path: Optional[str],
    output_path: Optional[str],
    input_scope: str,
    output_scope: str,
    force: bool,
    dry_run: bool,
) -> None:
    """Move skills from source to target (copy + delete from source).

    This command copies skills to the target and removes them from the source.
    Use with caution - this permanently deletes skills from the source location.

    \b
    Examples:
        skillboard move -i claude -o agent                    # global -> global
        skillboard move -i claude --input-scope local -o agent # local -> global
        skillboard move -i claude -o agent --output-scope local # global -> local
        skillboard move -i claude -o agent --dry-run          # Preview what would move
    """
    config = get_config()

    # Resolve source
    if input_path is None:
        console.print("[red]Error: Source is required. Use -i/--input option.[/red]")
        sys.exit(1)

    source_agent = input_path.lower()
    if source_agent in config.paths.list_paths():
        if input_scope == "local":
            source_path = Path(f"./.{source_agent}/skills")
        else:
            source_path = config.paths.get_path(source_agent)
    else:
        source_path = Path(input_path).expanduser()

    # Resolve target
    if output_path is None:
        console.print("[red]Error: Target is required. Use -o/--output option.[/red]")
        sys.exit(1)

    target_agent = output_path.lower()
    if target_agent in config.paths.list_paths():
        if output_scope == "local":
            target_path = Path(f"./.{target_agent}/skills")
        else:
            target_path = config.paths.get_path(target_agent)
    else:
        target_path = Path(output_path).expanduser()

    if not source_path.exists():
        console.print(f"[red]Error: Source does not exist: {source_path}[/red]")
        sys.exit(1)

    target_path.mkdir(parents=True, exist_ok=True)

    manager = SkillManager(source_path, target_path)
    skills = manager.get_source_skills()

    if not skills:
        console.print(f"[yellow]No skills found in {source_path}[/yellow]")
        return

    # Check for conflicts
    conflicts = []
    to_move = []

    for skill in skills:
        dest = target_path / skill.name
        if dest.exists():
            # Check if content is identical
            if are_skills_identical(skill.path, dest):
                # Same content, will skip
                conflicts.append((skill.name, "identical"))
            else:
                # Different content - real conflict
                conflicts.append((skill.name, "different"))
        else:
            to_move.append(skill)

    # Show summary
    console.print(f"\n[bold]Move Summary:[/bold] {source_path} → {target_path}")
    console.print(f"  Total skills in source: {len(skills)}")
    console.print(f"  Ready to move: {len(to_move)}")

    if conflicts:
        identical_count = sum(1 for _, status in conflicts if status == "identical")
        different_count = sum(1 for _, status in conflicts if status == "different")
        if identical_count:
            console.print(f"  Already exists (identical): {identical_count}")
        if different_count:
            console.print(f"  [yellow]Conflicts (different content): {different_count}[/yellow]")

    # Show what will be moved
    if to_move:
        console.print("\n[cyan]Skills to move:[/cyan]")
        for skill in to_move:
            console.print(f"  • {skill.name}")

    if not to_move:
        console.print("\n[dim]No skills to move.[/dim]")
        return

    if dry_run:
        console.print("\n[dim]--dry-run specified, no changes made.[/dim]")
        return

    # Safety confirmation
    console.print(
        f"\n[yellow]⚠️  Warning: This will PERMANENTLY DELETE skills from {source_path}[/yellow]"
    )
    confirm_msg = f"Move {len(to_move)} skill(s)?"

    try:
        import inquirer

        confirm_question = [inquirer.Confirm("confirm", message=confirm_msg, default=False)]
        confirm_answer = inquirer.prompt(confirm_question)
        if not confirm_answer or not confirm_answer["confirm"]:
            console.print("\n[yellow]Cancelled.[/yellow]")
            return
    except (KeyboardInterrupt, ImportError):
        console.print("\n[yellow]Cancelled.[/yellow]")
        return

    # Perform the move
    moved = 0
    skipped = 0
    errors = 0

    console.print("\n[bold]Moving skills...[/bold]\n")

    for skill in to_move:
        dest = target_path / skill.name

        # Handle existing files
        if dest.exists():
            if are_skills_identical(skill.path, dest):
                console.print(f"[dim]⏭ Skipping (identical): {skill.name}[/dim]")
                skipped += 1
                continue
            elif force:
                # Remove existing and continue
                try:
                    if dest.is_symlink():
                        dest.unlink()
                    else:
                        shutil.rmtree(dest)
                except Exception as e:
                    console.print(f"[red]✗ Error removing existing {skill.name}: {e}[/red]")
                    errors += 1
                    continue
            else:
                console.print(f"[yellow]⚠ Skipped (conflict): {skill.name}[/yellow]")
                skipped += 1
                continue

        # Copy to target
        try:
            shutil.copytree(skill.path, dest)
        except Exception as e:
            console.print(f"[red]✗ Error copying {skill.name}: {e}[/red]")
            errors += 1
            continue

        # Delete from source
        try:
            if skill.path.is_symlink():
                skill.path.unlink()
            else:
                shutil.rmtree(skill.path)
            console.print(f"[green]✓ Moved:[/green] {skill.name}")
            moved += 1
        except Exception as e:
            console.print(f"[red]✗ Error deleting {skill.name} from source: {e}[/red]")
            warning_msg = f"[yellow]  Warning: {skill.name} was copied to target"
            warning_msg += " but not removed from source[/yellow]"
            console.print(warning_msg)
            errors += 1

    console.print(f"\n[bold]Results:[/bold] {moved} moved, {skipped} skipped, {errors} errors")


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
