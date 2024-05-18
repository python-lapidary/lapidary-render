# Lapidary Render
## Synopsis

Lapidary is an in-python DSL for Web API clients.

Lapidary-render is a code generator that creates lapidary client code from an OpenAPI document.

## Installation

I recommend installing via `pipx`:

`pipx install lapidary-render`

Note that lapidary-render requires Python 3.12

## Usage

The `lapidary` command offers inline help and shell command completion. See `lapidary --help` for details.

### `lapidary init`

`lapidary init [--save] SCHEMA_PATH PROJECT_ROOT PACKAGE_NAME`

Initializes a project directory with a `pyproject.toml` file and optionally stores the OpenAPI document.

### `lapidary render`

`lapidary render [PROJECT_ROOT]`

Renders the client code in the project root. The default project root is the current directory.

All python files are generated in the `PROJECT_ROOT/gen` directory.

If a directory `PROJECT_ROOT/src/patches` exists, Lapidary will read all JSON and YAML files and apply them as JSONPatch
against the original OpenAPI file.

## Configuration

Lapidary can be configured with a `pyproject.yaml` file, under `[tool.lapidary]` path.

Only the `package` value is required, and it's set by `lapidary init`.

- package [str] - root package name.
- document_path [str] - path relative to the project root, or URL of the OpenAPI document.
- patches [str] - patches directory, under sources root [default = 'src/patches'].
