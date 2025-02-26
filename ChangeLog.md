# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


[Unreleased]

### Removed

- Support for JSONPatch

### Changed

- Breaking: openapi directory is now `${source root}/openapi`


## [0.11.1] - 2024-08-15

### Removed

- Removed support for generating exceptions

### Fixed

- Don't include body models of error responses in return types of operation methods
- Update `Metadata` annotation name from `Headers`


## [0.11.0] - 2024-08-14

### Added

- Wrap request headers (and cookies) in a model class

### Changed

- Replace return envelope with a tuple
- Generate new serialization style parameter

### Fixed

- Removed `Awaitable` from return type hints
- Fixed support for read/writeOnly fields - add default value `None`
- Added missing runtime dependency on httpx


## [0.10.1] - 2024-07-01

### Fixed

- Fix circular import error in generated response envelope module.
- Use the up-to-date version of lapidary when initializing projects.


## [0.10.0] - 2034-06-29

### Added

- HTTP security schemas supported by httpx;
- OAuth2 flows supported by httpx_auth;
- api-key authorization in cookie and query parameter;
- Progress bar for processing paths and rendering schema files;
- Support for response headers returned as response envelope model.
- Old files in `gen` directory are now removed during `render`.

### Changed

- Generate code for Lapidary 0.10.0

### Removed

- broken --cache option;


## [0.9.0](https://github.com/python-lapidary/lapidary/releases/tag/v0.9.0) - 2024-05-17
### Added
- Support for OAuth2 password flow.

### Changed
- Generate code for lapidary 0.9.0 .
- Migrated from Copier to Rybak for generating directory tree.

### Removed
- Temporary removed nicer package names to simplify code.
- Temporary removed support for paging.


## [0.8.0](https://github.com/python-lapidary/lapidary/releases/tag/v0.8.0) - 2023-01-02
### Added
- Support for returning array result as an async iterator.
- Support for paging (requires a dedicated plugin).

### Changed
- Replaced --format flag with --format-strict. The code is always formatted with black, --format-strict disables the fast mode.
- Changed the default openapi directory to src/openapi.
- Changed x-lapidary-model-type to x-lapidary-modelType, more in-line with OpenAPI naming.
- Changed generated package to a namespace to allow manual extensions packages. ApiClient and Auth import are now available form client module.
- Better reporting of missing operationId.

## [0.7.3](https://github.com/python-lapidary/lapidary/releases/tag/v0.7.3) - 2022-12-15
### Fixed
- Missing imports for request body types.

## [0.7.1](https://github.com/python-lapidary/lapidary/releases/tag/v0.7.1) - 2022-12-15
### Added
- Support for (global) api responses.
- Warning header to templates.
- Generate auth model to hold all parameters
- import ApiClient and Auth in __init__.py

### Changed
- Generate stubs instead of full operation methods.
- Migrated project to monorepo
- Changed some models to better suite a dynamic library.

### Fixed
- Fail on unsupported types
- Added templates to distribution package.

## [0.6.1](https://github.com/python-lapidary/lapidary/releases/tag/v0.6.1) - 2022-10-24
### Fixed
- handling default auth and invalid names.

## [0.6.0](https://github.com/python-lapidary/lapidary/releases/tag/v0.6.0) - 2022-10-24
### Changed
- Upgraded dependencies.

### Fixed
- Allow naming null enum values.
- missing quotes for bearer_format in the template.
- names and aliases of attributes.
- removed pprint calls from tests.
- name validation regex.
- generating nested schema classes.
- make param model class names camel case.

## [0.5.1](https://github.com/python-lapidary/lapidary/releases/tag/v0.5.1) - 2022-10-24
### Fixed
- issubclass for some typing.* types

## [0.5.0](https://github.com/python-lapidary/lapidary/releases/tag/v0.5.0) - 2022-10-03
### Added
- limited support for allOf schemas
- optional explicit names for enum values

### Changed
- Generated clients are now context managers
- Sort model attributes

### Fixed
- cache directory doesn't exist
- pydantic model Config classes
- read- and writeOnly properties were required
- inclusive/exclusive minimum mixed

## [0.4.0](https://github.com/python-lapidary/lapidary/releases/tag/v0.4.0) - 2022-09-29
### Added
- Added subcommands `update` and `init`, `update` reads configuration from pyproject.toml .
- ApiClient accepts base URL, the first server declared in schema is used as the default.
- Extended schema with global headers element; passing it as headers to httpx.AsyncClient().
- Added support for a single API Key authentication.
- Added support for naming schema classes
- Generate classes for schemas declared in-line under allOf, onyOf and oneOf.
- global responses
- Exception types

### Changed
- Rename project to Lapidary

### Fixed
- module name for response body schema class
- required params had default value ABSENT

## [0.3.1](https://github.com/python-lapidary/lapidary/releases/tag/v0.3.1) - 2022-09-20
### Fixed
- loading resources when installed from whl
- computing TypeRef hash
- writing pyproject to non-existent directory

## [0.3.0](https://github.com/python-lapidary/lapidary/releases/tag/v0.3.0) - 2022-09-20
### Changed
- Support Python 3.9

## [0.2.0](https://github.com/python-lapidary/lapidary/releases/tag/v0.2.0) - 2022-09-18
### Added
- Support simple oneOf schemas
- Support errata, a JSON Patch for the specification
- support for request and response body

### Changed
- lapis is now an executable

### Fixed
- Regex field value
- handling of type hints and imports

## [0.1.2](https://github.com/python-lapidary/lapidary/releases/tag/v0.1.2) - 2022-09-14
### Changed
- Renamed project due to a name conflict in PyPY


## [0.1.0](https://github.com/python-lapidary/lapidary/releases/tag/v0.1.0) - 2022-09-14
### Added
- Generate classes for schemas under components/schemas
- Generate partial client class with methods based on /paths/*/*

[Unreleased]: https://github.com/python-lapidary/lapidary-render/compare/v0.11.1...HEAD
[0.10.1]: https://github.com/python-lapidary/lapidary-render/compare/v0.11.0...v0.11.1
[0.10.1]: https://github.com/python-lapidary/lapidary-render/compare/v0.10.1...v0.11.0
[0.10.1]: https://github.com/python-lapidary/lapidary-render/compare/v0.10.0...v0.10.1
[0.10.0]: https://github.com/python-lapidary/lapidary-render/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/python-lapidary/lapidary-render/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/python-lapidary/lapidary-render/compare/v0.7.3...v0.8.0
[0.7.3]: https://github.com/python-lapidary/lapidary-render/compare/v0.7.1...v0.7.3
[0.7.1]: https://github.com/python-lapidary/lapidary-render/releases/tag/v0.7.1
