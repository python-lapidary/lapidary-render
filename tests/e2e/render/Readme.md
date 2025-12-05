# End to end tests

1. Create a project scaffolding (schema and pyproject.toml) for a test project (for example with `lapidary init`) in `init` directory
2. Copy the project scaffolding to `expected`
3. Render project in `expected` directory.
4. Examine the rendered code.
5. If code is satisfactory, commit the new code to git.
6. test_e2e.py will re-render the project and compare the result with the contents of `expected`.
