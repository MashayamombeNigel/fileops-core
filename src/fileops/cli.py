import sys
from pathlib import Path
import typer
from rich.console import Console

from fileops.config import load_config
from fileops.exceptions import ConfigError

app = typer.Typer(
    name="fileops",
    help="FileOps Core: Folder monitoring and event logging utility.",
    add_completion=False,
)

console = Console()

@app.command()
def monitor(
    config: Path = typer.Option(
        "config.yaml",
        "--config",
        "-c",
        help="Path to the YAML configuration file.",
    )
) -> None:
    """Start monitoring a folder for new files based on the provided configuration."""
    try:
        console.print(f"[bold blue][INFO][/bold blue] Loading configuration from [yellow]{config}[/yellow]...")
        cfg = load_config(str(config))
        
        console.print("[bold green][INFO][/bold green] Starting FileOps Core...")
        console.print(f"[bold green][INFO][/bold green] Watching directory: [yellow]{cfg.folder_path.resolve()}[/yellow]")
        console.print(f"[bold green][INFO][/bold green] Logs will be written to: [yellow]{cfg.log_path.resolve()}[/yellow]")
        console.print("[bold cyan][INFO][/bold cyan] Press Ctrl+C to exit.")
        
    except ConfigError as e:
        console.print(f"[bold red]❌ ERROR:[/bold red] {e}", style="red")
        sys.exit(2)
    except KeyboardInterrupt:
        console.print("\n[bold yellow][INFO][/bold yellow] Shutting down FileOps Core...")
        sys.exit(0)

def main() -> None:
    app()
