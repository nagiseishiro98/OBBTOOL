import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

console = Console()

# Default paths
search_path = "/storage/emulated/0/DARK_PAK/UNPACK_REPACK/UNPACK/game_patch_3.7.0.19729/unpack/"
output_path = "/storage/emulated/0/DARK_PAK/UNPACK_REPACK/UNPACK/game_patch_3.7.0.19729/repack/"

# Get hex replacements from user
hex_pairs = []
console.print("[cyan]Enter hex values in 'search_hex,replacement_hex' format (Type 'q' to finish):[/cyan]")
while True:
    user_input = input().strip()
    if user_input.lower() == "q":
        break
    if "," in user_input:
        search_hex, replacement_hex = user_input.split(",")
        hex_pairs.append((search_hex.strip(), replacement_hex.strip()))
    else:
        console.print("[red]Invalid format! Use 'search_hex,replacement_hex'[/red]")

# Process files
if not os.path.exists(output_path):
    os.makedirs(output_path)

modified_files = []

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("{task.percentage:>3.0f}%"),
    console=console,
) as progress:
    task = progress.add_task("[yellow]Processing files...[/yellow]", total=len(os.listdir(search_path)))

    for root, _, files in os.walk(search_path):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, "rb") as f:
                data = f.read()
            
            modified = False
            replaced_info = []

            for search_hex, replacement_hex in hex_pairs:
                search_bytes = bytes.fromhex(search_hex)
                replacement_bytes = bytes.fromhex(replacement_hex)
                if search_bytes in data:
                    data = data.replace(search_bytes, replacement_bytes)
                    modified = True
                    replaced_info.append(f"[green]{search_hex}[/green] ➝ [cyan]{replacement_hex}[/cyan]")

            if modified:
                output_file_path = os.path.join(output_path, file)
                with open(output_file_path, "wb") as f:
                    f.write(data)
                modified_files.append(file)
                console.print(f"[bold blue]Modified:[/bold blue] {file}")
                for info in replaced_info:
                    console.print(f"  {info}")

            progress.update(task, advance=1)

console.print("\n[bold magenta]✅ Hex replacement completed![/bold magenta]")

if modified_files:
    console.print("[bold green]Modified Files:[/bold green]")
    for file in modified_files:
        console.print(f"  [yellow]- {file}[/yellow]")
else:
    console.print("[bold red]No modifications were made.[/bold red]")