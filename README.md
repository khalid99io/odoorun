# odoorun

`odoorun` is a small command-line wrapper that finds an Odoo executable and
forwards your arguments to it. It lets you run Odoo from the project root or
from any directory nested inside the checkout.

## Installation

Install the current checkout as an isolated command with
[uv](https://docs.astral.sh/uv/):

```bash
uv tool install .
```

To update an existing installation after changing the source:

```bash
uv tool install --force .
```

## Usage

Run Odoo exactly as you normally would:

```bash
odoorun --database my_database --dev all
```

Arguments that are not odoorun commands are passed to Odoo unchanged.

odoorun searches for an executable `odoo-bin` in the current directory and
then each parent directory. If none is found, it looks for an `odoo` command on
your `PATH`. A project-local `odoo-bin` always takes precedence.

### Diagnostics

Check whether Odoo and the optional PostgreSQL client can be found:

```bash
odoorun doctor
```

Show odoorun's own help or version:

```bash
odoorun --help
odoorun --version
```

## Development

Run the test suite and basic source checks with:

```bash
uv run python -m unittest discover -s tests -v
uv run python -m compileall -q src tests
```
