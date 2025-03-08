"""Script to update .env file with timezone information."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from vocabulary_learning.core.constants import DEFAULT_TIMEZONE


def update_env():
    """Update .env file with timezone information."""
    console = Console()
    console.print(
        Panel.fit(
            "[bold blue]Timezone Configuration[/bold blue]\n\n"
            "This will add or update the timezone setting in your .env file.\n"
            f"For Finland, the timezone should be '{DEFAULT_TIMEZONE}'.",
            title="Timezone Setup",
            border_style="blue",
        )
    )

    # Get the .env file path
    env_path = Path(".env")

    # Read existing .env content
    env_content = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    try:
                        key, value = line.split("=", 1)
                        env_content[key.strip()] = value.strip()
                    except ValueError:
                        continue

    # Get timezone from user or use default
    timezone = Prompt.ask(
        "Enter your timezone", default=DEFAULT_TIMEZONE, show_default=True
    )

    # Update timezone in env_content
    env_content["TIMEZONE"] = timezone

    # Write back to .env file
    with open(env_path, "w", encoding="utf-8") as f:
        for key, value in env_content.items():
            f.write(f"{key}={value}\n")

    console.print(
        Panel.fit(
            f"[bold green]Timezone configuration updated![/bold green]\n"
            f"✓ Timezone set to: {timezone}\n"
            f"✓ Configuration saved to: {env_path.absolute()}",
            title="✓ Success",
            border_style="green",
        )
    )


if __name__ == "__main__":
    update_env()
