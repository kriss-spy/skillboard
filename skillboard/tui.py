"""Interactive CLI interface for skillboard using questionary.

Provides a searchable checkbox-based interface for selecting which skills to enable.
"""

from pathlib import Path
from typing import Any, Optional

import questionary
from questionary import Choice
from rich.console import Console

console: Console = Console()


def select_skills_interactive(
    skills: list[Any],
    source_path: Path,
    target_path: Optional[Path] = None,
    operation: str = "link",
    preselected: Optional[set[str]] = None,
) -> Optional[set[str]]:
    """Interactive skill selection with searchable TUI.

    Args:
        skills: List of Skill objects to select from
        source_path: Path to source directory
        target_path: Optional path to target directory
        operation: Type of operation (link, copy, move)
        preselected: Set of skill names to preselect

    Returns:
        Set of selected skill names, or None if cancelled
    """
    if not skills:
        console.print(f"[yellow]No skills found in {source_path}[/yellow]")
        return set()

    # Show header
    console.print(f"\n[bold]Managing skills from:[/bold] {source_path}")
    if target_path:
        console.print(f"[bold]Target directory:[/bold] {target_path}")

    console.print()

    # Build choices with descriptions and preselection via Choice objects
    choices: list[Choice] = []
    for skill in skills:
        if skill.description:
            desc = skill.description
            max_desc = 60
            if len(desc) > max_desc:
                desc = desc[: max_desc - 3].rstrip() + "..."
            title = f"{skill.name}  {desc}"
        else:
            title = skill.name

        checked = preselected is not None and skill.name in preselected
        choices.append(Choice(title=title, value=skill.name, checked=checked))

    # Ask user to select skills (questionary has built-in substring search)
    try:
        selected = questionary.checkbox(
            f"Select skills to {operation} (type to filter, space: toggle, enter: confirm)",
            choices=choices,
            use_search_filter=True,
            use_jk_keys=False,
        ).ask()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        return None

    if selected is None:
        console.print("\n[yellow]Cancelled.[/yellow]")
        return None

    if not selected:
        console.print("\n[dim]No skills selected.[/dim]")
        return set()

    result = set(selected)
    if result:
        console.print(f"\n[dim]{len(result)} skill(s) selected[/dim]")

    return result


def run_skill_tui(source_path: Path, target_path: Path) -> None:
    """Run interactive skill selection using questionary.

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
        confirm = questionary.confirm("Apply these changes?", default=True).ask()
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        return

    if confirm:
        enabled, disabled = manager.apply_changes(selected)

        console.print()
        if enabled:
            console.print(f"[green]✓ Enabled {len(enabled)} skill(s):[/green] {', '.join(enabled)}")
        if disabled:
            console.print(f"[red]✗ Disabled {len(disabled)} skill(s):[/red] {', '.join(disabled)}")
        console.print("\n[green]Done![/green]")
    else:
        console.print("\n[yellow]Cancelled.[/yellow]")
