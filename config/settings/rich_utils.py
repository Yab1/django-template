"""
Rich Logging Utilities for Enhanced Console Output.

This module provides utility functions and classes for leveraging Rich's
full capabilities in logging and console output.

Usage:
    from config.settings.rich_utils import log_panel, log_table, log_progress

    # Log with a fancy panel
    log_panel("Processing patients", "info")

    # Log a table
    log_table("Patient Statistics", headers=["Name", "Age"], rows=[...])

    # Use progress bar
    with log_progress("Processing...") as progress:
        task = progress.add_task("Task", total=100)
        ...
"""

import logging
from typing import Any, Dict, List, Optional

try:
    from rich.console import Console  # pyright: ignore[reportMissingImports]
    from rich.panel import Panel  # pyright: ignore[reportMissingImports]
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.syntax import Syntax  # pyright: ignore[reportMissingImports]
    from rich.table import Table  # pyright: ignore[reportMissingImports]
    from rich.tree import Tree  # pyright: ignore[reportMissingImports]

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def get_rich_console() -> Optional[Any]:
    """Get the Rich console instance if available."""
    if not RICH_AVAILABLE:
        return None

    try:
        from config.settings.logging import console

        return console
    except ImportError:
        return Console()


def log_panel(
    message: str,
    level: str = "info",
    title: Optional[str] = None,
    border_style: str = "blue",
    logger_name: str = "core",
) -> None:
    """
    Log a message inside a Rich panel for emphasis.

    Args:
        message: The message to display
        level: Log level (debug, info, warning, error, critical)
        title: Optional panel title
        border_style: Color for the panel border
        logger_name: Name of the logger to use

    Example:
        log_panel("Database migration completed successfully", "info",
                 title="Migration", border_style="green")
    """
    logger = logging.getLogger(logger_name)
    console = get_rich_console()

    if console and RICH_AVAILABLE:
        panel = Panel(message, title=title, border_style=border_style, expand=False)
        console.print(panel)
    else:
        # Fallback to regular logging
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(f"[{title}] {message}" if title else message)


def log_table(
    title: str,
    headers: List[str],
    rows: List[List[Any]],
    logger_name: str = "core",
    caption: Optional[str] = None,
) -> None:
    """
    Log data in a formatted table.

    Args:
        title: Table title
        headers: Column headers
        rows: Data rows
        logger_name: Name of the logger to use
        caption: Optional table caption

    Example:
        log_table(
            "User Statistics",
            headers=["Name", "Role", "Status"],
            rows=[["John", "Admin", "Active"], ["Jane", "User", "Active"]]
        )
    """
    logger = logging.getLogger(logger_name)
    console = get_rich_console()

    if console and RICH_AVAILABLE:
        table = Table(title=title, caption=caption, show_header=True, header_style="bold magenta")

        for header in headers:
            table.add_column(header, style="cyan")

        for row in rows:
            table.add_row(*[str(cell) for cell in row])

        console.print(table)
    else:
        # Fallback to regular logging
        logger.info(f"\n{title}")
        logger.info(" | ".join(headers))
        logger.info("-" * (len(" | ".join(headers))))
        for row in rows:
            logger.info(" | ".join(str(cell) for cell in row))


def log_dict(
    data: Dict[str, Any],
    title: Optional[str] = None,
    level: str = "info",
    logger_name: str = "core",
) -> None:
    """
    Log a dictionary with Rich formatting and syntax highlighting.

    Args:
        data: Dictionary to log
        title: Optional title
        level: Log level
        logger_name: Name of the logger to use

    Example:
        log_dict({"user": "john", "status": "active"}, title="User Data")
    """
    logger = logging.getLogger(logger_name)
    console = get_rich_console()

    if console and RICH_AVAILABLE:
        import json

        json_str = json.dumps(data, indent=2, default=str)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)

        if title:
            panel = Panel(syntax, title=title, border_style="green", expand=False)
            console.print(panel)
        else:
            console.print(syntax)
    else:
        # Fallback to regular logging
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(f"{title}: {data}" if title else str(data))


def log_tree(
    label: str,
    items: Dict[str, Any],
    logger_name: str = "core",
) -> None:
    """
    Log hierarchical data as a tree structure.

    Args:
        label: Root label
        items: Dictionary of items to display in tree
        logger_name: Name of the logger to use

    Example:
        log_tree("Project Structure", {
            "core": {"patients": ["models", "views"], "fhir": ["models"]},
            "config": ["settings", "urls"]
        })
    """
    logger = logging.getLogger(logger_name)
    console = get_rich_console()

    if console and RICH_AVAILABLE:
        tree = Tree(f"[bold cyan]{label}[/bold cyan]")

        def add_items(parent, data):
            if isinstance(data, dict):
                for key, value in data.items():
                    branch = parent.add(f"[yellow]{key}[/yellow]")
                    add_items(branch, value)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, (dict, list)):
                        add_items(parent, item)
                    else:
                        parent.add(f"[green]{item}[/green]")
            else:
                parent.add(f"[green]{data}[/green]")

        add_items(tree, items)
        console.print(tree)
    else:
        # Fallback to regular logging
        logger.info(f"{label}: {items}")


def log_progress(description: str = "Processing..."):
    """
    Create a Rich progress bar for long-running operations.

    Args:
        description: Progress bar description

    Returns:
        Progress instance (use as context manager)

    Example:
        with log_progress("Processing patients") as progress:
            task = progress.add_task("[cyan]Processing...", total=len(patients))
            for patient in patients:
                # Do work
                progress.update(task, advance=1)
    """
    if RICH_AVAILABLE:
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=get_rich_console(),
        )
    # Return a dummy context manager that does nothing

    class DummyProgress:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def add_task(self, *args, **kwargs):
            return 0

        def update(self, *args, **kwargs):
            pass

    return DummyProgress()


def log_syntax(
    code: str,
    language: str = "python",
    title: Optional[str] = None,
    line_numbers: bool = True,
    theme: str = "monokai",
    logger_name: str = "core",
) -> None:
    """
    Log code with syntax highlighting.

    Args:
        code: Code string to display
        language: Programming language for syntax highlighting
        title: Optional title
        line_numbers: Whether to show line numbers
        theme: Color theme
        logger_name: Name of the logger to use

    Example:
        log_syntax('def hello():\\n    print("world")', "python", title="Example Code")
    """
    logger = logging.getLogger(logger_name)
    console = get_rich_console()

    if console and RICH_AVAILABLE:
        syntax = Syntax(
            code,
            language,
            theme=theme,
            line_numbers=line_numbers,
            word_wrap=False,
        )

        if title:
            panel = Panel(syntax, title=title, border_style="blue", expand=False)
            console.print(panel)
        else:
            console.print(syntax)
    else:
        # Fallback to regular logging
        logger.info(f"{title}:\n{code}" if title else code)


def log_success(message: str, logger_name: str = "core") -> None:
    """Log a success message with green checkmark."""
    logger = logging.getLogger(logger_name)
    console = get_rich_console()

    if console and RICH_AVAILABLE:
        console.print(f"[bold green]✓[/bold green] {message}")
    else:
        logger.info(f"✓ {message}")


def log_error(message: str, logger_name: str = "core") -> None:
    """Log an error message with red X."""
    logger = logging.getLogger(logger_name)
    console = get_rich_console()

    if console and RICH_AVAILABLE:
        console.print(f"[bold red]✗[/bold red] {message}")
    else:
        logger.error(f"✗ {message}")


def log_warning(message: str, logger_name: str = "core") -> None:
    """Log a warning message with yellow warning symbol."""
    logger = logging.getLogger(logger_name)
    console = get_rich_console()

    if console and RICH_AVAILABLE:
        console.print(f"[bold yellow]⚠[/bold yellow] {message}")
    else:
        logger.warning(f"⚠ {message}")


# Example usage function for documentation
def _example_usage():
    """Example usage of Rich logging utilities."""
    # Panel logging
    log_panel(
        "System initialized successfully",
        level="info",
        title="✨ System Status",
        border_style="green",
    )

    # Table logging
    log_table(
        "Patient Summary",
        headers=["ID", "Name", "Status", "Last Visit"],
        rows=[
            ["P001", "John Doe", "Active", "2024-01-15"],
            ["P002", "Jane Smith", "Inactive", "2023-12-20"],
        ],
        caption="Total: 2 patients",
    )

    # Dictionary logging
    log_dict(
        {
            "patient_id": "P001",
            "name": "John Doe",
            "age": 45,
            "conditions": ["diabetes", "hypertension"],
        },
        title="Patient Details",
    )

    # Tree logging
    log_tree(
        "Patient Care Team",
        {
            "Primary Care": ["Dr. Smith", "Nurse Johnson"],
            "Specialists": {
                "Cardiology": ["Dr. Brown"],
                "Endocrinology": ["Dr. Davis", "Dr. Wilson"],
            },
        },
    )

    # Progress bar
    with log_progress("Processing patients") as progress:
        task = progress.add_task("[cyan]Loading records...", total=100)
        for i in range(100):
            # Simulate work
            import time

            time.sleep(0.01)
            progress.update(task, advance=1)

    # Syntax highlighting
    log_syntax(
        '''
def calculate_bmi(weight, height):
    """Calculate BMI."""
    return weight / (height ** 2)
        '''.strip(),
        language="python",
        title="BMI Calculator",
    )

    # Status messages
    log_success("Patient record created successfully")
    log_warning("Patient has missing contact information")
    log_error("Failed to connect to external API")


if __name__ == "__main__":
    _example_usage()
