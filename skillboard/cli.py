"""Command-line interface for skillboard.

Provides commands for:
- link: Create symbolic links to skills (interactive)
- list: Show available skills in warehouse
- list-path: Show configured skill paths
- init: Initialize directories
- copy: Copy skills (not symlink)
- move: Move skills between locations
- read: Display skill content
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
from .paths import (
    ensure_target_directory,
    resolve_link_source,
    resolve_source_path,
    resolve_target_path,
    validate_source_exists,
)
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
        skillboard link -o claude          # Interactive link to Claude
        skillboard link -o agent --no-tui  # Just list skills
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
    "link_all",
    is_flag=True,
    help="Link from both global and local sources.",
)
@click.option(
    "--verbose",
    "verbose_mode",
    is_flag=True,
    help="Show full table of skills (default: summary only).",
)
@click.option("--no-tui", is_flag=True, help="Run in non-TUI mode (list skills only).")
def link(
    input_path: Optional[str],
    output_path: Optional[str],
    input_scope: str,
    output_scope: str,
    link_all: bool,
    verbose_mode: bool,
    no_tui: bool,
) -> None:
    """Create symbolic links to skills in target directory.

    This command creates symbolic links from source to target,
    allowing you to toggle skills on/off for different agents.

    \b
    Examples:
        skillboard link -o claude                    # global -> global
        skillboard link -i claude -o agent           # global claude -> global agent
        skillboard link -i claude --input-scope local -o agent   # local claude -> global agent
        skillboard link -i claude -o agent --output-scope local  # global claude -> local agent
        skillboard link -i claude --all -o agent     # (global+local) claude -> global agent
    """
    config = get_config()

    # Resolve source and target paths
    source = resolve_link_source(input_path, input_scope, link_all, config)
    target = resolve_target_path(output_path, output_scope, config)
    validate_source_exists(source)
    ensure_target_directory(target)

    # Info message about symbolic links
    console.print(f"[dim]Creating symbolic links from {source} to {target}...[/dim]\n")

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
            console.print(f"\n[bold]Link Summary:[/bold] {source} → {target}")
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
@click.option(
    "--migrate",
    is_flag=True,
    help="Migrate old .agent paths to .agents (v0.2.0 to v0.3.0)",
)
def init(migrate: bool) -> None:
    """Initialize skillboard configuration and directories.

    Creates the warehouse directory and any missing agent directories.
    Also saves the configuration file.

    Use --migrate to update old .agent paths to .agents (breaking change in v0.3.0).
    """
    from skillboard.config import SkillPaths

    config = get_config()

    # Check for old .agent paths that need migration
    migrated = []
    if migrate:
        console.print("[bold]Migrating paths from .agent to .agents...[/bold]\n")

        # Create new SkillPaths to get the correct defaults
        correct_paths = SkillPaths()

        # Check each path and migrate if needed
        for name in ["warehouse", "agent"]:
            old_path = getattr(config.paths, name)
            new_path = getattr(correct_paths, name)

            if ".agent/" in str(old_path) and ".agents/" in str(new_path):
                # Update the path
                setattr(config.paths, name, new_path)
                migrated.append((name, old_path, new_path))
                console.print(f"[yellow]✓ Migrated:[/yellow] {name}")
                console.print(f"    From: {old_path}")
                console.print(f"    To:   {new_path}")

        if migrated:
            console.print()

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

    if migrated:
        console.print(f"\n[yellow]Migrated {len(migrated)} path(s) from .agent to .agents[/yellow]")
        console.print(
            "[dim]Old directories still exist. You can manually move skills if needed.[/dim]"
        )
    elif paths_created:
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
@click.option(
    "--all",
    is_flag=True,
    help="Copy all skills without interactive selection.",
)
def copy(
    input_path: Optional[str],
    output_path: Optional[str],
    input_scope: str,
    output_scope: str,
    all: bool,
) -> None:
    """Copy skills from source to target (not symlink).

    Interactive by default - use --all to copy all skills without selection.

    \b
    Examples:
        skillboard copy -i claude -o agent                    # Interactive select
        skillboard copy -i claude -o agent --all              # Copy all
        skillboard copy -i claude --input-scope local -o agent # local -> global
        skillboard copy -i claude -o agent --output-scope local # global -> local
    """
    from .tui import select_skills_interactive

    config = get_config()

    # Resolve source and target paths
    source_path = resolve_source_path(input_path, input_scope, config)
    target_path = resolve_target_path(output_path, output_scope, config)
    validate_source_exists(source_path)
    ensure_target_directory(target_path)

    manager = SkillManager(source_path, target_path)
    skills = manager.get_source_skills()

    if not skills:
        console.print(f"[yellow]No skills found in {source_path}[/yellow]")
        return

    # Select skills interactively unless --all is specified
    if all:
        selected_skills = {skill.name for skill in skills}
        console.print(f"[dim]Copying all {len(selected_skills)} skills...[/dim]\n")
    else:
        selected = select_skills_interactive(
            skills,
            source_path,
            target_path,
            operation="copy",
        )
        if selected is None:
            return
        selected_skills = selected
        if not selected_skills:
            console.print("\n[yellow]No skills selected.[/yellow]")
            return

    # Confirm before copying
    if not all:
        try:
            import inquirer
        except ImportError:
            console.print("[red]Error: 'inquirer' package is required for interactive mode.[/red]")
            console.print("Install with: pip install inquirer")
            return

        try:
            confirm_q = [
                inquirer.Confirm(
                    "confirm", message=f"Copy {len(selected_skills)} skill(s)?", default=True
                )
            ]
            confirm_a = inquirer.prompt(confirm_q)
            if not confirm_a or not confirm_a["confirm"]:
                console.print("\n[yellow]Cancelled.[/yellow]")
                return
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled.[/yellow]")
            return

    console.print(f"\n[bold]Copying {len(selected_skills)} skills...[/bold]\n")

    copied = 0
    skipped = 0
    errors = 0

    for skill in skills:
        if skill.name not in selected_skills:
            continue
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
@click.option(
    "--all",
    is_flag=True,
    help="Move all skills without interactive selection.",
)
def move(
    input_path: Optional[str],
    output_path: Optional[str],
    input_scope: str,
    output_scope: str,
    force: bool,
    dry_run: bool,
    all: bool,
) -> None:
    """Move skills from source to target (copy + delete from source).

    Interactive by default - use --all to move all skills without selection.
    Use with caution - this permanently deletes skills from the source location.

    \b
    Examples:
        skillboard move -i claude -o agent                    # Interactive select
        skillboard move -i claude -o agent --all              # Move all
        skillboard move -i claude --input-scope local -o agent # local -> global
        skillboard move -i claude -o agent --output-scope local # global -> local
        skillboard move -i claude -o agent --dry-run          # Preview what would move
    """
    from .tui import select_skills_interactive

    config = get_config()

    # Resolve source and target paths
    source_path = resolve_source_path(input_path, input_scope, config)
    target_path = resolve_target_path(output_path, output_scope, config)
    validate_source_exists(source_path)
    ensure_target_directory(target_path)

    manager = SkillManager(source_path, target_path)
    skills = manager.get_source_skills()

    if not skills:
        console.print(f"[yellow]No skills found in {source_path}[/yellow]")
        return

    # Select skills interactively unless --all is specified
    if all:
        selected_skills = {skill.name for skill in skills}
        console.print(f"[dim]Moving all {len(selected_skills)} skills...[/dim]\n")
    else:
        selected = select_skills_interactive(
            skills,
            source_path,
            target_path,
            operation="move",
        )
        if selected is None:
            return
        selected_skills = selected
        if not selected_skills:
            console.print("\n[yellow]No skills selected.[/yellow]")
            return

    # Dry run check
    if dry_run:
        console.print("\n[bold]Dry Run - Would move:[/bold]")
        for skill_name in selected_skills:
            console.print(f"  • {skill_name}")
        console.print("\n[dim]No changes made.[/dim]")
        return

    # Safety confirmation
    console.print(
        f"\n[yellow]⚠️  Warning: This will PERMANENTLY DELETE skills from {source_path}[/yellow]"
    )

    try:
        import inquirer
    except ImportError:
        console.print("[red]Error: 'inquirer' package is required for interactive mode.[/red]")
        console.print("Install with: pip install inquirer")
        return

    try:
        confirm_q = [
            inquirer.Confirm(
                "confirm", message=f"Move {len(selected_skills)} skill(s)?", default=False
            )
        ]
        confirm_a = inquirer.prompt(confirm_q)
        if not confirm_a or not confirm_a["confirm"]:
            console.print("\n[yellow]Cancelled.[/yellow]")
            return
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        return

    # Perform the move using atomic move with rollback
    moved = 0
    skipped = 0
    errors = 0

    console.print("\n[bold]Moving skills...[/bold]\n")

    for skill in skills:
        if skill.name not in selected_skills:
            continue

        success, message = manager.move_skill(skill.name, force=force)

        if success:
            if message == "identical":
                console.print(f"[dim]⏭ Skipping (identical): {skill.name}[/dim]")
                skipped += 1
            else:
                console.print(f"[green]✓ Moved:[/green] {skill.name}")
                moved += 1
        else:
            if message == "conflict":
                console.print(f"[yellow]⚠ Skipped (conflict): {skill.name}[/yellow]")
                skipped += 1
            else:
                console.print(f"[red]✗ Error with {skill.name}: {message}[/red]")
                errors += 1

    console.print(f"\n[bold]Results:[/bold] {moved} moved, {skipped} skipped, {errors} errors")


@cli.command()
@click.argument("skill_name")
@click.option(
    "-a",
    "--agent",
    type=str,
    help="Agent to read from (claude, agent, gemini, opencode, antigravity).",
)
@click.option(
    "--scope",
    type=click.Choice(["global", "local"], case_sensitive=False),
    default="global",
    help="Scope: global (~/.<agent>/skills) or local (./.<agent>/skills).",
)
@click.option(
    "--github",
    is_flag=True,
    help="Read from .github/skills directory.",
)
def read(skill_name: str, agent: Optional[str], scope: str, github: bool) -> None:
    """Display skill content for quick reference.

    Shows the SKILL.md content and file listing without opening an editor.

    \b
    Examples:
        skillboard read 3d-web-experience                    # Read from global agent
        skillboard read my-skill -a claude                   # Read from claude
        skillboard read my-skill --scope local               # Read from local
        skillboard read my-skill --github                    # Read from .github/skills
    """
    config = get_config()

    # Determine skill path
    if github:
        skill_path = Path(".github/skills") / skill_name
    elif agent:
        agent_lower = agent.lower()
        if agent_lower in config.paths.list_paths():
            if scope == "local":
                skill_path = Path(f"./.{agent_lower}/skills") / skill_name
            else:
                skill_path = config.paths.get_path(agent_lower) / skill_name
        else:
            console.print(f"[red]Unknown agent: {agent}[/red]")
            return
    else:
        # Default: check global agent path
        skill_path = config.paths.agent / skill_name
        if not skill_path.exists():
            # Try local
            skill_path = Path("./.agents/skills") / skill_name

    if not skill_path.exists():
        console.print(f"[red]Skill not found: {skill_name}[/red]")
        console.print(f"[dim]Searched: {skill_path}[/dim]")
        return

    # Display skill info
    console.print(f"\n[bold]{'─' * 50}[/bold]")
    console.print(f"[bold cyan]{skill_name}[/bold cyan]")
    console.print(f"[bold]{'─' * 50}[/bold]\n")

    # Read SKILL.md if it exists
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text(encoding="utf-8")
        # Show first 50 lines
        lines = content.split("\n")[:50]
        console.print("[bold]SKILL.md:[/bold]\n")
        for line in lines:
            console.print(line)
        if len(content.split("\n")) > 50:
            console.print("\n[dim]... (truncated, showing first 50 lines)[/dim]")
    else:
        console.print("[dim]No SKILL.md found[/dim]")

    # List files in skill directory
    console.print(f"\n[bold]{'─' * 50}[/bold]")
    console.print("[bold]Files:[/bold]\n")
    files = sorted(skill_path.rglob("*"))
    for file in files:
        if file.is_file():
            rel_path = file.relative_to(skill_path)
            console.print(f"  • {rel_path}")

    console.print(f"\n[bold]{'─' * 50}[/bold]\n")


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
