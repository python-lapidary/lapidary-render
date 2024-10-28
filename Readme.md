# Lapidary render

[![.github/workflows/test.yml](https://github.com/python-lapidary/lapidary-render/actions/workflows/test.yml/badge.svg)](https://github.com/python-lapidary/lapidary-render/actions/workflows/test.yml)

Lapidary-render is a program that generates Python Web API clients from OpenAPI documents.

## Why

OpenAPI is a machine readable description of Web APIs. A large subset of it is very well suited for automatic translation to a client code.

## How

Lapidary render uses [Jinja](https://jinja.palletsprojects.com/) to generate client code, but most of the translation from OpenAPI to python is implemented in python itself. This makes it easier to read and maintain the generator itself.

Instead of generating large pieces of code that convert data and call http libraries, Lapidary generates code that uses [Lapidary runtime library](https://github.com/python-lapidary/lapidary). It's also a way to greatly simplify the code, at the expense of small runtime overhead related to processing method signatures.
