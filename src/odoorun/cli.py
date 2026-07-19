import typer

cli = typer.Typer(
    add_completion=False,
)


@cli.command()
def doctor() -> None:
    """Show diagnostic information."""
    print("Doctor command")
