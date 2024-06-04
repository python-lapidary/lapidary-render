# Lapidary Render
## Synopsis

Lapidary-render is a code generator that creates client code from an OpenAPI document.

## Project Goals

- [x] Deliver IDE-friendly client code that simplifies communication with API servers.

- [x] The generator code should be simple.

    Lapidary-render does most of the processing in Python, only leaving the rendering to Jinja templates.

- [x] Client code should be simple.

    The generated code uses the `lapidary` DSL library, which makes the client code DRY and similar in style to API servers that use Litestar or FastAPI.

- [ ] Compatible changes to the OpenAPI document should result in compatible changes to the generated code.

    Whenever possible, generated names should not depend on elements position, or the presence or absence of other elements.

    *Starting from version 1.0; terms and conditions apply.*

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

If the patches directory (`PROJECT_ROOT/src/patches` by default) exists, Lapidary will read all JSON and YAML files
and apply them as JSONPatch files against the original OpenAPI file.

## Configuration

Lapidary can be configured with a `pyproject.yaml` file of the client project, under `[tool.lapidary]` key.

- package - root package name.
- document_path - path of the OpenAPI document, relative to the project root.
- origin - URL of the OpenAPI document, used when document_path is missing, or when `servers` is not defined, or the first server URL is a relative path.
- patches - patches directory [default = 'src/patches'].

At least one of `document_path` and `origin` is required. Saving OpenAPI document in the project is recommended for repeatable builds.
