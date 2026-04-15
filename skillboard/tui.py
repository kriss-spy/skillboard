"""Interactive CLI interface for skillboard using inquirer.

Provides a simple checkbox-based interface for selecting which skills to enable.
"""

import sys
from pathlib import Path
from typing import Any, Optional

from rich.console import Console

console = Console()


def select_skills_interactive(
    skills: list[Any],
    source_path: Path,
    target_path: Optional[Path] = None,
    operation: str = "link",
    preselected: Optional[set[str]] = None,
) -> Optional[set[str]]:
    """Interactive skill selection with TUI.

    Args:
        skills: List of Skill objects to select from
        source_path: Path to source directory
        target_path: Optional path to target directory
        operation: Type of operation (link, copy, move)
        preselected: Set of skill names to preselect

    Returns:
        Set of selected skill names, or None if cancelled
    """
    try:
        import inquirer
    except ImportError:
        console.print("[red]Error: 'inquirer' package is required.[/red]")
        console.print("Install it with: pip install inquirer")
        sys.exit(1)

    if not skills:
        console.print(f"[yellow]No skills found in {source_path}[/yellow]")
        return set()

    # Show header
    console.print(f"\n[bold]Managing skills from:[/bold] {source_path}")
    if target_path:
        console.print(f"[bold]Target directory:[/bold] {target_path}")

    # Show compact summary
    console.print(f"\n[bold]Summary:[/bold] {len(skills)} skills available\n")

    # Show first 10 skills as compact list
    if len(skills) <= 10:
        console.print("[dim]Available skills:[/dim]")
        for skill in skills:
            console.print(f"  • {skill.name}")
    else:
        console.print("[dim]First 10 skills:[/dim]")
        for skill in skills[:10]:
            console.print(f"  • {skill.name}")
        console.print(f"[dim]  ... and {len(skills) - 10} more[/dim]")

    console.print()

    # Prepare choices with "[Select All]" option
    skill_names = [skill.name for skill in skills]
    choices = ["[Select All]"] + skill_names

    # Determine default selection:
    # - If preselected is explicitly provided (even if empty), use it
    # - If preselected is None (not provided), default to empty (no selection)
    if preselected is None:
        default_selection = []
    else:
        default_selection = list(preselected)

    # Ask user to select skills
    questions = [
        inquirer.Checkbox(
            "selected",
            message=f"Select skills to {operation} (space: toggle, enter: confirm)",
            choices=choices,
            default=default_selection,
        ),
    ]

    try:
        answers = inquirer.prompt(questions)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        return None

    if answers is None:
        console.print("\n[yellow]Cancelled.[/yellow]")
        return None

    selected = set(answers["selected"])

    # Handle "[Select All]" option
    if "[Select All]" in selected:
        selected = set(skill_names)
        console.print(f"\n[dim]All {len(selected)} skills selected[/dim]")
    elif not selected:
        console.print("\n[dim]No skills selected.[/dim]")
        return set()

    return selected


def run_skill_tui(source_path: Path, target_path: Path) -> None:
    """Run interactive skill selection using inquirer.

    Displays a table of current skills and prompts the user to select
    which skills to enable via checkboxes.

    Args:
        source_path: Path to warehouse (source of truth)
        target_path: Path to target directory where symlinks will be created
    """
    from skillboard.manager import SkillManager

    manager = SkillManager(source_path, target_path)
    skills = manager.scan_skills()

    # Track currently enabled skills for preselection
    currently_enabled = {skill.name for skill in skills if skill.is_enabled}

    selected = select_skills_interactive(
        skills,
        source_path,
        target_path,
        operation="link",
        preselected=currently_enabled,
    )

    if selected is None:
        return

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
    try:
        import inquirer

        confirm_questions = [
            inquirer.Confirm(
                "confirm",
                message="Apply these changes?",
                default=True,
            ),
        ]
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
