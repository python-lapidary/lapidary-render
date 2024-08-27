# Plugins

There are cases where the original OpenAPI Description (OAD) document is not sufficient (or even faulty) and needs to be amended,
but for various reasons, be it legal or practical, we can't or don't want to modify it.

Lapidary render allows client projects to provide python code extensions that can modify their OpenAPI Descriptions on the fly.

## Usage

Plugins are classes
implementing [`lapidary.render.plugins.ProcessorPlugin`](https://github.com/python-lapidary/lapidary-render/blob/develop/src/lapidary/render/plugins.py)
protocol, and can make changes to the `dict` form of OAD.

This allows them to make any changes as long as the resulting object is a valid OpenAPI Description.

```python
# plugins/plugins.py
class MyPlugin:
    async def process_mapping(self, model: dict, config: lapidary.render.Config, project_root: anyio.Path) -> Mapping:
        ...
```

In order to work, they must be listed in `pyproject.toml`, in the form `package:class`:

```toml
[tool.lapidary]
plugins = [
    'plugins:MyPlugin'
]
```

`plugins` directory acts as "package path" (it's temporarily added to `sys.path`), so we don't include it in the package name. Also you can't import any python modules outside of that directory, or any external dependencies, other than `lapidary.render`.

In any case plugins must be completely predictable and mustn't generate anything dynamically (e.g. based on external resources, other the OAD file).

# Tutorial

## Use case

Let's say we have this OAD:

```yaml
paths:
  /my_operation:
    get:
      operationId: get_many_by_id_in
      parameters:
      - name: id__in
        in: query
        description: 'A comma-separated list of UUIDs'
        schema:
          type: string
```

`lapidary render` generates this python code:

```python
class ApiClient:
    async def get_many_by_id_in(
        self: Self,
        id__in_q: Annotated[str, Query('id__in')]
    ):
        pass
```

The default style for query parameters is `form, explode`, which looks like `?id__in=uuid1&id__in=uuid2`,
while the server expects something like `?id__in=uuid1,uuid2`.
Before we can call this function, we need to convert the data.

```python
client: ApiClient
ids: Iterable[UUID]

await client.get_many_by_id_in(','.join(str(id_) for id_ in ids))
```

Let's try to improve the OAD so we don't have to write this code for every parameter.

## Solution with JSON Patch

When the document has one or few instances like this, we can apply a JSON Path to fix it.

First we need to add the JSONPatch plugin to the project's `pyproject.toml`:

```toml
[tool.lapidary]
plugins = [
    'lapidary.render.plugins:JSONPatchPlugin',
]
```

`JSONPatchPlugin` will load all yaml and json files in `/src/patches` directory and apply them as JSONPatch to the OAD.

The

```yaml
# src/patches/my_operation.yaml
- op: replace
  path: /paths/~1my_operation/get/parameters/0/schema
  value:
    type: array
    items:
      type: string
      format: uuid
```
The server expects `?id__in=uuid1,uuid2` which happens to fit style `form, no-explode`. `form, explode` is the default for `query`...
```yaml
- op: add
  path: /paths/~1my_operation/get/parameters/0/explode
  value: false
```

Now the Description would look like this:
```yaml
paths:
  /my_operation:
    get:
      operationId: get_many_by_id_in
      parameters:
      - name: id__in
        in: query
        description: 'A comma-separated list of UUIDs'
        explode: false
        schema:
          type: array
          items:
            type: string
            format: uuid
```

Which in turns results in this python code:

```python
class ApiClient:
    async def get_many_by_id_in(
        self: Self,
        id__in_q: Annotated[list[UUID], Query('id__in_q', style: Form)]
    ):
        pass
```

Other serialization styles explained in
the [OpenAPI guide](https://swagger.io/docs/specification/serialization/).

## Solution with a python plugin

JSON Patch is great, until you have to apply the same change tens, hundreds or thousands of times.

For such situation we can use a python plugin:

```python
# plugins/plugins.py
class MyPlugin:
    async def process_mapping(self, model: dict, _, _1) -> dict:
        for path_obj in model['paths'].values():
            for op in path_obj.values():
                for parameter in op.get('parameters', ()):
                    schema = parameter['schema']
                    if not parameter['name'].endswith('__in') or schema['type'] != 'string':
                        continue

                    parameter['schema'].update({
                        'type': 'array',
                        'items': {
                            'type':' string',
                            'format': 'uuid',
                        },
                    })
                    parameter['explode'] = False
        return model
```

Let's replace JSONPatch with our plugin.

```toml
# pyproject.toml
[tool.lapidary]
plugins = [
    'plugins:MyPlugin'
]
```

This example has the same effect as the previous one, except it's applied to every parameter of very operation, if the parameter name ends with '__in' and `type` is `string`.
