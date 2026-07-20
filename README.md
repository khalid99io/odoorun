# odoorun

`odoorun` is a portable command-line launcher and inspection tool for Odoo
development projects. It discovers the appropriate Odoo executable, prepares
addon paths, forwards ordinary Odoo options, completes database and module
names, and provides read-only database/addon inspection commands.

No symlink, alias, or machine-specific path is required. Run
`odoorun completion install` once to enable Bash auto-completion.

## Features

- Run a project-local `odoo-bin`, a linked-venv `odoo`, or `odoo` on `PATH`.
- Run from a project root or any nested directory.
- Configure standard and custom addon paths automatically.
- Complete PostgreSQL database names after `-d`/`--database`.
- Complete module names after `-u`/`--update` and `-i`/`--init`.
- Complete odoorun commands, options, and fixed option values.
- List Odoo databases and detect their versions.
- List core/custom addon manifests and optionally show database module state.
- Produce human-readable tables, tab-separated text, or JSON.

## Requirements

- Python 3.10 or newer.
- `psql` for database completion, `db list`, and database-aware `addon list`.

Launching Odoo and listing addons from the filesystem do not require `psql`.

## Installation

Install the published package as an isolated command:

```bash
uv tool install odoorun
```

Or install with pip:

```bash
python -m pip install odoorun
```

Install the latest source directly from GitHub:

```bash
uv tool install git+https://github.com/khalid99io/odoorun.git
```

Install or refresh a local development checkout:

```bash
uv tool install --force .
```

## Quick start

Run Odoo with ordinary Odoo options:

```bash
odoorun -d my_database --dev=all
odoorun -d my_database -u sale_management
```

Add custom directories to an Odoo source checkout. Relative `-a` paths are
resolved from the checkout's parent directory:

```bash
odoorun -a custom-addons,enterprise -d my_database
```

Use Odoo's native addon preference unchanged:

```bash
odoorun --addons-path="addons,custom-addons" -d my_database
```

The short `o` command is optional. If you configure `alias o=odoorun`, the
examples below can use `o`; otherwise use `odoorun` directly.

## How executable discovery works

odoorun selects the first available executor in this order:

1. An executable `odoo-bin` in the current directory or a parent directory.
2. An Odoo executor in the linked or configured project venv, such as
   `~/venvs/<project>/bin/odoo`.
3. An `odoo` command available on `PATH`.

For source checkouts, the built-in `addons` directory is passed automatically.
For linked-venv projects, `--addons=odoo/addons` is added unless the user
provides `--addons`, `--addons-path`, or an equivalent value explicitly.

If the project and venv names differ, configure discovery with:

```bash
export ODOORUN_VENV_NAME=my-project-venv
export ODOORUN_VENV_ROOT="$HOME/venvs"
```

odoorun invokes the venv executable directly, so activating the venv is not
required for the Odoo child process. A child process cannot alter the parent
shell prompt; prompt decoration remains a shell responsibility.

## Command reference

### Odoo passthrough

```text
odoorun [ODOO_OPTIONS]
```

Arguments whose first item is not an odoorun tool command are passed to the
discovered Odoo executable. The `-a` option is odoorun's source-checkout
convenience and is converted into the effective native `--addons-path`.

### `odoorun doctor`

```text
odoorun doctor
```

Displays the working directory, discovered Odoo executable, and whether `psql`
is available. It does not modify the project or start Odoo.

### `odoorun completion`

```text
odoorun completion [bash|install]
```

- `bash` prints the generated Bash integration script.
- `install` idempotently adds `source <(odoorun completion bash)` to `~/.bashrc`.

Run the installer once and open a new Bash terminal:

```bash
odoorun completion install
```

Command and option completion is available for `odoorun` and `o`:

```bash
o d<Tab>                         # db, doctor
o db <Tab>                       # list
o addon list --s<Tab>            # --source, --state
o addon list --source c<Tab>     # core, custom
o addon list --state in<Tab>     # installed
o db list --format j<Tab>        # json
```

Database and module completion is also registered for direct Odoo commands:
`odoo`, `odoo-bin`, and `./odoo-bin`.

Database examples:

```bash
o -d demo<Tab>
odoorun --database=demo<Tab>
```

Module examples, including comma-separated values:

```bash
o -d my_database -u sale_m<Tab>,bas<Tab>
o -d my_database -i custom_m<Tab>
```

Database completion uses `psql` and respects PostgreSQL environment variables
such as `PGHOST`, `PGPORT`, `PGUSER`, `PGDATABASE`, and `PGPASSWORD`. Module
completion finds directories containing `__manifest__.py` or `__openerp__.py`
in source, project, explicit, and linked-venv addon roots.

### `odoorun db list`

```text
odoorun db list [OPTIONS]
```

Options:

- `--odoo-version VERSION`: keep Odoo databases whose installed `base` module
  version starts with `VERSION`, such as `19` or `19.0`.
- `--all`: include regular PostgreSQL and inaccessible databases.
- `--format table|plain|json`: select the output format; default is `table`.
- `--no-header`: hide headings in table/plain output.

Examples:

```bash
odoorun db list
odoorun db list --odoo-version 19
odoorun db list --all --format json
```

By default, only databases recognized as Odoo databases are shown. Detection
uses `ir_module_module`, and the displayed Odoo version comes from the installed
`base` module.

### `odoorun addon list`

```text
odoorun addon list [OPTIONS]
```

Options:

- `-d, --database DATABASE`: query `ir_module_module` and annotate filesystem
  addons with their state/version in that database.
- `--source all|core|custom`: filter by addon-root origin.
- `--state all|installed|uninstalled|upgrade`: filter by database state;
  non-`all` values require `-d`.
- `--installed`: shortcut for `--state installed`; requires `-d`.
- `--custom`: shortcut for `--source custom`.
- `--core`: shortcut for `--source core`.
- `--addons-path PATHS`: override discovery with a native comma-separated Odoo
  addon path.
- `-a PATHS`: add comma-separated custom directories to source-checkout
  discovery.
- `--format table|plain|json`: select the output format; default is `table`.
- `--no-header`: hide headings in table/plain output.

Examples:

```bash
odoorun addon list
odoorun addon list --source core
odoorun addon list --custom
odoorun addon list -d my_database
odoorun addon list -d my_database --installed --custom
odoorun addon list --addons-path="addons,../enterprise"
```

Addon discovery always starts from filesystem directories. Supplying `-d`
does not search addons inside a database; it only adds database state/version
information and enables state filtering.

### `odoorun --version`

Print the installed odoorun version and exit:

```bash
odoorun --version
```

Every tool command has focused help:

```bash
odoorun completion --help
odoorun db list --help
odoorun addon list --help
```

## PostgreSQL connection behavior

Database features execute read-only queries through `psql`. Standard libpq
configuration is respected, including environment variables, service files,
and `.pgpass`. Passwords are not accepted as odoorun command-line options.

## Development

Run tests and source compilation checks:

```bash
uv run python -m unittest discover -s tests -v
uv run python -m compileall -q src tests
```

The GitHub CI workflow installs, tests, compiles, and builds the project on
Python 3.10, 3.11, 3.12, and 3.13 for pushes and pull requests.

## License and publishing

odoorun is released under the MIT License. The source repository is:

https://github.com/khalid99io/odoorun

PyPI releases use the GitHub Actions Trusted Publisher workflow. Before a new
release, update the version in `pyproject.toml`, verify CI, and push a matching
version tag.
