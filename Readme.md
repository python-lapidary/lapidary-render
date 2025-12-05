# Lapidary render

[![.github/workflows/test.yml](https://github.com/python-lapidary/lapidary-render/actions/workflows/test.yml/badge.svg)](https://github.com/python-lapidary/lapidary-render/actions/workflows/test.yml)

Lapidary-render is a program that generates Python Web API clients from OpenAPI documents.

## Why

It's a good practice to encapsulate Web API client code in functions or classes and methods,

If the Web API exposes an OpenAPI document, you can reduce the manual effort by generating the client code.

## How

Install Lapiary-render, for example with pipx

```shell
pipx install lapidary-render
```

Start your project

```shell
lapidary init --save https://example.com/openapi.json project_dir my_api_client
```

Generate code:
```shell
cd project_dir
lapidary render
```

Check the [documentation](https://lapidary.dev/lapidary-render/) for more details.
