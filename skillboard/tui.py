"""Interactive CLI interface for skillboard using inquirer.

Provides a simple checkbox-based interface for selecting which skills to enable.
"""

import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def run_skill_tui(source_path: Path, target_path: Path) -> None:
    """Run interactive skill selection using inquirer.

    Displays a table of current skills and prompts the user to select
    which skills to enable via checkboxes.

    Args:
        source_path: Path to warehouse (source of truth)
        target_path: Path to target directory where symlinks will be created
    """
    try:
        import inquirer
    except ImportError:
        console.print("[red]Error: 'inquirer' package is required.[/red]")
        console.print("Install it with: pip install inquirer")
        sys.exit(1)

    from skillboard.manager import SkillManager

    manager = SkillManager(source_path, target_path)
    skills = manager.scan_skills()

    if not skills:
        console.print(f"[yellow]No skills found in {source_path}[/yellow]")
        return

    # Track currently enabled skills
    currently_enabled = {skill.name for skill in skills if skill.is_enabled}

    console.print(f"\n[bold]Managing skills from:[/bold] {source_path}")
    console.print(f"[bold]Target directory:[/bold] {target_path}")

    # Show compact summary instead of full table for many skills
    enabled_count = sum(1 for s in skills if s.is_enabled)
    available_count = len(skills) - enabled_count

    summary = f"\n[bold]Summary:[/bold] {len(skills)} total, {enabled_count} enabled, "
    summary += f"{available_count} available\n"
    console.print(summary)

    # Only show full table if 10 or fewer skills, or show first 10
    if len(skills) <= 10:
        table = Table(title="Available Skills")
        table.add_column("Status", justify="center")
        table.add_column("Skill Name")
        table.add_column("Type")

        for skill in skills:
            status = "✓" if skill.is_enabled else "✗"
            link_type = "symlink" if skill.is_symlink else ("copy" if skill.is_enabled else "-")
            table.add_row(
                f"[green]{status}[/green]" if skill.is_enabled else f"[dim]{status}[/dim]",
                skill.name,
                link_type,
            )

        console.print(table)
    else:
        # Show first 10 skills as compact list
        console.print("[dim]First 10 skills:[/dim]")
        for skill in skills[:10]:
            status = "✓" if skill.is_enabled else "✗"
            status_fmt = f"[green]{status}[/green]" if skill.is_enabled else f"[dim]{status}[/dim]"
            console.print(f"  {status_fmt} {skill.name}")
        console.print(f"[dim]  ... and {len(skills) - 10} more[/dim]")

    console.print()

    # Ask user to select skills
    questions = [
        inquirer.Checkbox(
            "selected",
            message="Select skills (space: toggle, enter: confirm)",
            choices=[skill.name for skill in skills],
            default=list(currently_enabled),
        ),
    ]

    try:
        answers = inquirer.prompt(questions)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        return

    if answers is None:
        console.print("\n[yellow]Cancelled.[/yellow]")
        return

    selected = set(answers["selected"])

    # Show what will change
    to_enable = selected - currently_enabled
    to_disable = currently_enabled - selected

    if to_enable:
        console.print(f"\n[green]Will enable:[/green] {', '.join(sorted(to_enable))}")
    if to_disable:
        console.print(f"[red]Will disable:[/red] {', '.join(sorted(to_disable))}")

    if not to_enable and not to_disable:
        console.print("\n[dim]No changes needed.[/dim]")
        return

    # Confirm
    confirm_questions = [
        inquirer.Confirm(
            "confirm",
            message="Apply these changes?",
            default=True,
        ),
    ]

    try:
        confirm_answer = inquirer.prompt(confirm_questions)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        return

    if confirm_answer and confirm_answer["confirm"]:
        enabled, disabled = manager.apply_changes(selected)

        console.print()
        if enabled:
            console.print(f"[green]✓ Enabled {len(enabled)} skill(s):[/green] {', '.join(enabled)}")
        if disabled:
            console.print(f"[red]✗ Disabled {len(disabled)} skill(s):[/red] {', '.join(disabled)}")
        console.print("\n[green]Done![/green]")
    else:
        console.print("\n[yellow]Cancelled.[/yellow]")
