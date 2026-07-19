# odoorun

`odoorun` is a portable command-line launcher for Odoo. It finds an Odoo
executable from the current project (or a parent directory), prepares the
appropriate addons path, and forwards the remaining arguments unchanged.

It does not require symlinks, shell aliases, a modified `.bashrc`, or a
machine-specific configuration.

## Requirements

- Python 3.10 or newer
- An Odoo installation or source checkout
- `psql` is optional and is used only for database completion/diagnostics

Odoo and PostgreSQL are external dependencies; `odoorun` does not install or
configure them.

## Installation

### Recommended: install from PyPI

Once published, install it on any supported machine with:

```bash
uv tool install odoorun
```

Or use pip:

```bash
python -m pip install odoorun
```

### Install directly from GitHub

```bash
uv tool install git+https://github.com/khalid99io/odoorun.git
```

### Install a local checkout (development)

```bash
uv tool install .
```

After changing the checkout, refresh the installed command:

```bash
uv tool install --force .
```

## Usage

Run from an Odoo source checkout or any directory below it:

```bash
odoorun -d my_database --dev=all
```

The short command `o` is optional and is not installed by this package. If
desired, add your own alias or shell function:

```bash
alias o=odoorun
```

### Virtual-environment projects

For a project directory named `my-project`, `odoorun` looks for:

```text
~/venvs/my-project/bin/odoo
```

When found, it adds `--addons=odoo/addons` automatically. If the virtual
environment has a different name, configure it without editing the package:

```bash
export ODOORUN_VENV_NAME=my-project-venv
export ODOORUN_VENV_ROOT="$HOME/venvs"
```

The tool invokes the venv executable directly; sourcing `activate` is not
required for the launched Odoo process. A subprocess cannot change the parent
shell's prompt, so prompt decoration remains a shell responsibility.

### Odoo source checkouts

For a checkout containing an executable `odoo-bin`, the built-in `addons`
directory is passed automatically. Additional addon directories can be listed
with `-a` or `--addons-path`; relative paths are resolved from the checkout's
parent directory:

```bash
odoorun -a custom-addons,enterprise -d my_database
```

Each directory must exist. Missing directories are reported before Odoo starts.

## Diagnostics

```bash
odoorun doctor
odoorun --help
odoorun --version
```

## Development

```bash
uv run python -m unittest discover -s tests -v
uv run python -m compileall -q src tests
```

## Publishing

The source repository is hosted on GitHub:

https://github.com/khalid99io/odoorun

To publish releases on PyPI, create a PyPI account, configure a trusted
publisher for this GitHub repository (recommended), build the package, and
upload it with `twine` or a GitHub Actions release workflow. A GitHub account
is required for the repository; a separate PyPI account is required to publish
the `odoorun` package name.

Before the first release, update the version in `pyproject.toml`, add release
notes, and verify the package in a clean virtual environment.
