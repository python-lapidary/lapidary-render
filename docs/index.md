# Lapidary Render
## Synopsis

Lapidary-render is a code generator that creates client code from an OpenAPI document.

## Project Goals

- [x] Deliver IDE-friendly client code that simplifies communication with API servers.

- [x] The generator code should be simple.

    Generator processes data in three stages

    1. Enhance and transform OpenAPI to a structure more close resembling python model structure
    2. Convert the enhanced OpenAPI to a metamodel
    3. Convert the metamodel to a syntax tree

- [x] Client code should be simple.

    The generated code uses the `lapidary` DSL library, which makes the client code DRY and similar in style to API servers that use Litestar or FastAPI.

- [ ] Compatible changes to the OpenAPI document should result in compatible changes to the generated code.

    Whenever possible, generated names should not depend on elements position, or the presence or absence of other elements.

    *Starting from version 1.0; terms and conditions apply.*

## Installation

I recommend installing via `pipx`:

`pipx install lapidary-render`

Note that lapidary-render requires Python 3.13

## Usage

The `lapidary` command offers inline help and shell command completion. See `lapidary --help` for details.

### `lapidary init`

`lapidary init [--save] SCHEMA_PATH PROJECT_ROOT PACKAGE_NAME`

Initializes a project directory with a `pyproject.toml` file and optionally stores the OpenAPI document.

### `lapidary render`

`lapidary render [PROJECT_ROOT]`

Renders the client code in the project root. The default project root is the current directory.

All python files are generated in the `PROJECT_ROOT/gen` directory.

## Configuration

Lapidary can be configured with a `pyproject.yaml` file of the client project, under `[tool.lapidary]` key.

package
: root package name.

document_path
: path of the OpenAPI document, relative to the project root.

origin
: URL of the OpenAPI document, used when document_path is missing, or when `servers` is not defined, or the first server URL is a relative path.

extra_sources
: list of additional source roots for manually written python files.

At least one of `document_path` and `origin` is required. Saving OpenAPI document in the project is recommended for repeatable builds.
