## JSON Schema

Representing JSON Schema as python types, aiming at producing types that can express no less values than the corresponding schema can validate.
Another goal is to keep models as backwards compatible as much as possible, when the schema changes in a compatible way.

The examples below use YAML notation of JSON Schema version draft-wright-json-schema-00.

Python examples use python 3.10 (PEP 604) type hints syntax.

### Open and closed world

JSON Schema is an open-world language: an empty schema accepts any JSON value, and adding keywords restricts the set of valid values.

Standard Python class instances are dictionaries at runtime, but Pydantic objects and Python static type checking (mypy, pyright)
are closed-world: an empty class accepts nothing, and adding fields expands what can be stored.

This open/closed-world contrast is the main problem of mapping JSON Schema to Python types. The transformations in this document are
an application of set theory to resolve it:

`python model = any JSON type - declared JSON Schema constraints`


### Type definitions and names

In JSON Schema, schemas are often defined in-line, immediately describing body, field or property, or they can be referenced by path using
`$ref` - these two methods are interchangeable, though typically reused schemas are defined under `components/schemas` element.
Schemas are generally anonymous (unnamed) although they can be identified by their path.

In python, types might be required to be named (classes), or they might be anonymous (parametrized types).
Parametrized types are always derived from named types, and they themselves may be named too (type aliases).

For each schema python code will need the following:

- fully qualified name - name and package (file to store the class, package to import it from) - derived from schema path,
- optional type parameters (pydantic field properties, lists item type, union element types, etc.) - derived from schema itself,
- in case of object schemas, a class definition - derived from schema properties.


## Cross-type constraints

Most of the constraints are type-specific (they apply only to values of a certain type or types).

The exceptions are:

- nullable: extend types by type `null`, but only if type is specified in that schema
- enum: only allow values specified in the list

That means most constraints can be processed separately, which is useful when they occur together with `allOf`, `oneOf`, `anyOf` and `not`.

### `type` and `nullable`

1. Since Schema object validates any JSON value, let's consider it a Union type:

        {}

    =>

        dict | list | float | int | str | bool | None

    or

        pydantic.JsonValue

2. In OpenAPI, `type` key, if present, can only accept a single type

    | JSON type | Python    |
    |-----------|-----------|
    | null      | `None`    |
    | boolean   | `bool`    |
    | integer   | `int`     |
    | number    | `float`   |
    | string    | `str`     |
    | array     | `list`    |
    | object    | `dict`    |

    e.g.

        type: integer

    =>

        int

3. `nullable` keyword can be used to extend the type with `None`

        type: integer
        nullable: true

    =>

        int | None

4. Any combination of types is possible with `anyOf`/`oneOf`.

        anyOf:
        - type: string
        - type: integer
          nullable: true

    =>

        str | int | None


## `enum`


### `enum` as `Literal`

1. Scalar `enum` could be translated literally

        enum:
        - true
        - false
        - FileNotFound

    =>

        Literal[True, False, 'FileNotFound']

    or grouped by type:

        Union[
            Literal[True, False],
            StrLiteral['FileNotFound'],
        ]

### `enum` as `enum.Enum`

1. Both scalar and non-scalar literals could be translated as python enums, but that would require names

        type: object
        enum:
        - key: value

    =>

        class ${schema}Enum(Enum):
            elem${idx} = $schema(key='value')

    This solution could introduce unintentional breaking changes when simply changing order of enum elements, unless enum elements were named with some extension keyword.

    It would work for scalar values

        enum:
        - true
        - false
        - FileNotFound

    =>

        class ${schema}Enum(Enum):
            value_true = True
            value_false = False
            value_FileNotFound = 'FileNotFound'

### Non-scalar enum values

Non-scalar enum values don't have natural names, but a hash of stringified value could be used.

Also creating an arbitrary number of objects, that might never be used will be expensive and wasteful, so factory methods could be used:

```yaml
enum:
- id: 1
  name: LoL
  slug: league-of-legends
```

=>

```python
def value_5d9b08cdd67689d128f7c30f885f273c():
    return CurrentVideogame(
        id=1,
        name='LoL',
        slug='league-of-legends',
    )
```

The problem with this solution is that the name changes when keys or any value changes, which may or may not be desirable from the user-developer perspective.

## Scalar constraints

1. Constraint keywords can be grouped by type (both numeric types together) and processed as such.

        maximum: 10
        maxLength: 10
        anyOf:
        - type: string
        - type: integer
    =>

        anyOf:
        - type: string
          maxLength: 10
        - type: integer
          maximum: 10

    =>

        Union[
            Annotated[str, Field(max_length=10)],
            Annotated[int, Field(le=10)]
        ]

1. There might be more than one element for a given type:

        anyOf:
        - type: integer
          maximum: 10
        - type: integer
          minimum: 20

    =>

        Union[
            Annotated[int, Field(le=10)],
            Annotated[int, Field(ge=20)],
        ]

1. The above is different than this, which is a bottom type (no object can validate against it, since no number can be greater than 20 _and_ smaller than 10):

        type: integer
        maximum: 10
        minimum: 20

1. As somewhat a special case, this schema is alright:

        maximum: 10
        minimum: 20

    =>

        str | bool | dict | list | None

    Numeric types are excluded since they can't validate against this schema.

2. allOf applies the most restrictive set of constraints.

        allOf:
        - maximum: 10
        - maximum: 20

    =>

        maximum: 10


## Object constraints

1. JSON type `object` could be mapped to `dict` or, with some limitations to `TypedDict` or a model in one of data modelling libraries like dataclasses, pydantic msgspec, etc. Here the choice falls on pydantic, which seems the most featured.

1. In the most trivial (from python's perspective) case properties can be translated to instance fields in a model class:

        additionalProperties: false
        properties:
          name:
            type: string
          required:
          - name

    =>

        class Model(BaseModel):
          name: string

1. In case of default object schema, it's impossible to say anything about its fields.

    It could be mapped as `dict` but then adding a property would cause an incompatible change in the python code. Instead, it can be translated to empty model class with `extra = 'allow'`

        type: object

    =>

        class Model(BaseModel):
            model_config = pydantic.ConfigDict(
                extra='allow'
            )

    The problem with this form is that there's no way to know what to do with the extra object values.
    Since an empty schema has the default:

        additionalProperties: true

    which is the same as

        additionalProperties: {}

    which means such a definition is indefinitely recursive. We could model it as a simple dict (in union with other types) or a common model class

        class AnyObject(BaseModel):
            model_config = pydantic.ConfigDict(
                extra='allow'
            )

    but in either case adding a property (particularly a non-required property, which is a compatible change) leads to an incompatible change in the python model.

### `additionalProperties`

The value is processed as a JSON Schema.

1. `true`

    Allows extra fields of any type. See above.

1. `false`

    Forbids extra fields

        class $name(BaseModel):
            model_config = pydantic.ConfigDict(
                extra='forbid'
            )

1. A schema definition.

    Allows extra fields and, if a non-empty schema is used, generate type:

        type: object
        additionalProperties:
            type: integer

    =>

        class $name(BaseModel):
            model_config = pydantic.ConfigDict(
                extra='allow'
            )

            __extra__: dict[str, int]


### writeOnly, readOnly and non-required properties

Non-required means the same as optional in English, but `Optional` is a type in python, so avoiding it for clarity.

`writeOnly` and `readOnly` apply to schemas that are used in other schemas' properties.
When one of the keywords is used, the property that schema describes only applies when the value is sent to or received from (respectively) the server, and should not be transferred in the other way.

One option to implement it would be a class hierarchy - parent class with all properties, child class for request model and one for response model. This would get complicated with nested properties.

Non-required properties are properties not listed in `required` list of the containing schema.

writeOnly, readOnly and non-required can be made optional fields in python, even though readOnly and writeOnly properties may be required.

```yaml
type: object
properties:
   alpha:
      type: string
      readOnly: true
   beta:
      type: string
      writeOnly: true
   gamma:
      type: string
   required:
   -  alpha
   -  beta
```
=>

```python
class $name:
    alpha: str | None = None  # required in client response
    beta:  str | None = None  # required in client request
    gamma: str | None = None  # not required
```

## `array`s

Two keywords describe arrays

## `anyOf`

When `anyOf` keyword is used, the instance validates as long as it validates against one of sub-schemas, while the validation results against other children schemas are ignored.

For example, scalar constraints can be transformed to `Union` type

        type: integer
        anyOf:
        - maximum: 10
        - minimum: 20

    =>

        Union[
            Annotated[int, Field(le=10)],
            Annotated[int, Field(ge=20)],
        ]

### `anyOf` and `enum`

1. If `enum` is in `anyOf` sub-schemas, the values are summed as sets.


## `oneOf`

1. Per the specification `oneOf` keyword validates when the value validates against exactly one child schema.

    In practice it's not the case, and `oneOf` is used as type union, typically with disjoint sub-schemas, but sometimes erroneously with overlapping ones.

    For this reason it could be processed just like `anyOf`, although separately: values must validate against one of `oneOf` children _and_ one of `anyOf` children.


1. With only `type` constraint, `anyOf` and `oneOf` are equivalent, since any value can be of only one type:

        oneOf:
        - type: integer
        - type: string

        anyOf:
        - type: integer
        - type: string

    =>

        int | str

1. With more than one constraint for the same `type`, interpreting them (also for python) gets more complex

        type: integer
        oneOf:
        - maximum: 20
        - minimum: 10

    is equivalent to:

        type: integer
        oneOf:
        - allOf:
          - maximum: 20
          # not minimum: 10
          - maximum: 10
            exclusiveMaximum: true
        - allOf:
          - minimum: 10
          # not maximum: 20
          - minimum: 20
            exclusiveMinimum: true

    Since 10 < 20, it reduces to:

        type: integer
        oneOf:
        # matches minimum: 10 but not maximum: 20
        - minimum: 20
          exclusiveMinimum: true
        # matches maximum: 20 but not minimum: 10
        - maximum: 10
          exclusiveMaximum: true

## `allOf`

1. When processing `allOf` in schema, the goal is generating a schema that can be directly represented as a python model.

    The original schema must be replaced by a simplified equivalent.

1. When `allOf` keyword is used, a value must validate against the schema that contains it as well as all children schemas in `allOf`.

    All schemas are of equal priority, and conflicting use of keywords makes it invalid for translating to a python model type.

    1. The constraints in the top schema could be pushed down under `allOf` to get a homogenous `allOf` schema:

            type: integer
            allOf:
            -   minimum: 10
            -   multipleOf: 2

        =>

            allOf:
            -   type: integer
            -   minimum: 10
            -   multipleOf: 2

    1.  Constraints in `allOf` can be also pulled up to the top schema

            allOf:
            -   type: integer
            -   minimum: 10
            -   multipleOf: 2

        =>

            type: integer
            minimum: 10
            multipleOf: 2

        Constraint keywords behave differently when used with `allOf`. For example the most restrictive constraint win in case of scalar constraints, enums use set intersection
        but `oneOf` elements are deep-merged.

    Because it doesn't matter whether constraints are in the parent schema or pushed down to a sub-schema, the paper assumes that constraints are pushed down to simplify the language.

1. When `allOf` contains more than two sub-schemas, they can be processed sequentially

        schema1 & schema2 & schema3 = (schema1 & schema2) & schema3

### `allOf` and `type`

`allOf` applies a set intersection to `type`

    # implied type: $any
    allOf:
    - type: integer

=>

    type: integer

This is a bottom type:

    allOf:
    - type: integer
    - type: string

#### `allOf` and `nullable`

The result is nullable only if every sub-schema either skips `type` or has `nullable: true`.

```yaml
allOf:
-   type: string
    nullable: true
    ...
-   type: string
    nullable: true
    ...
```

### `allOf` and `enum`

If `enum` is in `allOf` sub-schemas, the output value is a set intersection of `enum` in all sub-schemas that have one.

### `allOf` and scalar constraints

1. When keywords don't repeat between sub-schemas, they can be simply merged.
1. When the same keyword is used more than once, the more constraining value wins.
1. When merging `maximum` and `minimum` values, `exclusiveMinimum` and `exclusiveMaximum` must be considered. If the keyword (`minimum` or `maximum`) has the same value, the one with `exclusive*: true` is more constraining.

### `allOf` and `object` constraints

1. Determining named properties:

    1. Take all property names from all sub-schemas.
    1. If there are sub-schemas with `additionalProperties: false`, discard property names that don't match any of their sub-schema property names.

1. Determining named property schemas

    For each named property the resulting schema is calculated by merging

      - named property schemas from all sub-schemas with that property, and
      - `additionalProperties` schemas from all sub-schemas that don't have the named property.

### `allOf` and `array` constraints

1. `additionalItems` is not supported in OpenAPI 3.0
1. `items` schemas are merged as if they were direct children of `allOf`.

        allOf:
        -   type: array
            items:
                maxLength: 10
        -   type: array
            items:
                maxLength: 20

    =>

        type: array
        items:
            allOf:
            -   maxLength: 10
            -   maxLength: 20

    =>

        type: array
        items:
            maxLength: 10

### Nested `allOf`

Since schemas can be pushed down and pulled up around `allOf`, sub-schemas of nested `allOf` pulled up which results in flattening the schema.

    allOf:
    -   allOf:
        -   type: integer
        -   minimum: 10
    -   multipleOf: 2

=>

    allOf:
    -   type: integer
    -   minimum: 10
    -   multipleOf: 2

### `allOf` and (`oneOf` or `anyOf`)

When `oneOf` and/or `anyOf` keywords are present, the validated value must match one of sub-schemas of `anyOf` _and_ one of sub-schemas of `oneOf`.
A python model must be generated for each combination of constraints, meaning the schema needs to be a cartesian product of:

- the entire schema that's not part of `oneOf`/`anyOf`
- sub-schemas under `oneOf` of each `allOf` sub-schemas
- sub-schemas under `anyOf` of each `allOf` sub-schemas

## `not`

1. The keyword can be interpreted as a reversal or, in some cases removal of constraints, depending on the constraint.


        not:
            minimum: 10

    =>

        maximum: 10
        exclusiveMaximum: true

1. It can be used to exclude a set or a range of values:

        minimum: 1
        maximum: 10
        not:
            maximum: 9
            minimum: 9
        type: integer

    =>

        type: integer
        oneOf:
        - minimum: 1
          maximum: 8
        - minimum: 10
          maximum: 10

    =>

        Union[
            Annotated[int, Field(ge=1, le=65533)],
            Annotated[int, Field(ge=65535, le=65535)],
        ]

    Note: this is the only use of `not` I could find in apis.guru catalogue.

## Keyword interactions
### `type` and `enum`

When `enum` and `type` are both used, any value present in `enum` but whose type is not present in `type` wouldn't validate.
Similarly, any value of allowed type, but absent from enum wouldn't validate.

Therefore `enum` keyword determines allowed types, and it's a set intersection of the two.


### `type` and constraints

If `type` is defined, constraints for types not listed are discarded.

The default `type` value (not defined) means all types are valid and all constraints are considered.

### `type` and `anyOf` or `oneOf`

1. When evaluating `type` with either `oneOf` or `anyOf`, the two are equivalent, since no JSON value can be of more than one type

        anyOf:
        - type: integer
        - type: string

    or

        oneOf:
        - type: integer
        - type: string
    =>

        int | str


### `object` and `oneOf`/`anyOf`

The properties declared directly in the schema are always present (even if nullable, but excluding `writeOnly`/`readOnly`),
but properties on `oneOf`/`anyOf` sub-schemas form optional groups, one of which must be present (even if elements of the group may be themselves optional).

This suggests two possible solutions:
1. Create a class for each combination of properties. When OpenAPI properties or parameters are translated to python, represent such schema as a Union type.
1. Create a class for every element of `anyOf`/`oneOf` (use cartesian product if both are present) and add a synthetic Union field in the class representing the parent schema.

Creating a parent class from the parent schema seems to only complicate things when both parent and sub-schemas define the same property.

1. Creating a `Union` type

    All constraints in the parent schema can be pushed down to `allOf`/`oneOf` so that it describes a `Union` type

        components:
            schemas:
                mySchema:
                    type: object
                    properties:
                        myProp:
                            anyOf:
                            -   type: string
                            -   $ref: '#components/schemas/mySchema'

    =>

        components:
            schemas:
                mySchema:
                    type: object
                    properties:
                        myProp:
                            anyOf:
                            -   type: string
                            -   $ref: mySchema


    =>

        class mySchema:
            myProp: str | mySchema

#### `type: object`, `allOf` and circular references

JSON Schema specification section 7 on `$ref` warns against scenario like this:

```yaml
Alice:
    properties:
        myProp1:
            type: string
    allOf:
    -   #/Bob
Bob:
    properties:
        myProp2:
            type: string
    allOf:
    -   #/Alice
```

Actually both schemas could be represented as the same class:

```python
class Schema:
    myProp1: str|None
    myProp2: str|None
```

Instance of Schema class will validate against both schemas

#### `type: object`, `oneOf`/`anyOf` and `allOf`

Sub-schemas in `allOf/oneOf` and `allOf/anyOf` must validate separately and cannot be merged.

    type: object
    properties:
        alpha:
            type: integer
    additionalProperties: false
    required:
    -   alpha
    allOf:
    - oneOf:
      - properties:
        alpha:
          multipleOf: 2
      - properties:
        alpha:
          multipleOf: 3
    - oneOf:
      - properties:
          alpha:
            maximum: 10
      - properties:
        alpha:
          minimum: 20

Objects that validate would need validate against one of sub-schemas in the first child _and_ one of sub-schemas in the second child.
In this case the object would need a `int` field named 'alpha' that can be either divisible by 2 _or_ 3 and at the same time either less or equal 10 or more or equal to 20.

This really describes four possibilities:

1. divisible by 2 and less or equal 20
2. divisible by 2 and more or equal 10
3. divisible by 3 and less or equal 20
4. divisible by 3 and more or equal 10

We can see we need to restructure the schema by applying cartesian product and merging the inner allOf sub-schemas:

    type: object
    properties:
        alpha:
            type: integer
    additionalProperties: false
    required:
    -   alpha
    oneOf:
    -   properties:
            alpha:
                multipleOf: 2
                maximum: 20
    -   properties:
            alpha:
                multipleOf: 2
                minimum: 10
    -   properties:
            alpha:
                multipleOf: 3
                maximum: 20
    -   properties:
            alpha:
                multipleOf: 3
                minimum: 10

Also, properties get deep-merged:

    type: object
    properties:
        alpha:
            type: integer
    additionalProperties: false
    required:
    -   alpha
    properties:
        alpha:
            oneOf:
            -   multipleOf: 2
                maximum: 20
            -   multipleOf: 2
                minimum: 10
            -   multipleOf: 3
                maximum: 20
            -   multipleOf: 3
                minimum: 10

Now we can see a simple python class like this:

    class $name:
        alpha: Union[
            Annotated[int, Field(...)],
            Annotated[int, Field(...)],
            Annotated[int, Field(...)],
            Annotated[int, Field(...)],
        ]

## Conflicting schemas

1. There are many ways of declaring schemas that no value could validate. Such schemas aren't invalid, but the part describing a single type the keywords apply to, must be discarded.

        minimum: 20
        maximum: 10

    =>

        oneOf:
        -   type: boolean
        -   type: string
        -   type: object
        -   type: array

    but this schema never validates, so can't be translated to a type:

        type: integer
        minimum: 20
        maximum: 10

1. Conflicting enum values

    `enum` keyword applies to all types so a conflict here makes the schema impossible to translate into a type:`

        allOf:
        -   enum: ["red"]
        -   enum: ["green"]

## Annotations

Schemas could produce annotations (type hints) and python types or type aliases (type aliases are not currently implemented).

Whenever a schema is _used_, in an object property, or in case of OpenAPI, operation parameter, request or response body, in python an annotation is used.

```yaml
Alice:
    properties:
        bob:
            type: object
            properties:
                prop1:
                    type: string
```

```python

class Alice(ModelBase):
    bob: bob
```

But in order for `bob` to be valid, it also needs to be defined:

```python
class bob
    prop1: str
```

Scalar schemas could produce type aliases, but currently are used inline.

```yaml
Alice:
    type: object
    properties:
        prop1:
            type: integer
            maximum: 20
```

```python
class Alice:
    prop1: Annotated[int, Le(20)]
```

## Generic types

1. JSON Schema only supports generic arrays and maps:

```yaml
sequence:
  type: array
  items:
    type: string
map:
  type: object
  additionalProperties:
    type: number
```

=>

```python
sequence: list[str]
map: dict[str, float]
```

There's no way of directly representing a generic python class:

```python
class Envelope[T]:
    id: uuid.UUID
    payload: T


class Customer:
    ...


data: Envelope[Customer]
```

can only be represented as concretised schemas:

```yaml

Customer:
   type: object

Envelope:
   type: object
   properties:
      id:
         type: string
         format: uuid
      payload:
         type: object

CustomerEnvelope:
   allOf:
   - $ref: '#/schemas/Envelope'
   - properties:
        payload:
           $ref: '#/schemas/Customer'
```

## Type naming

### Name mangling

To produce a valid Python identifier from an arbitrary string:

1. replace any literal `u_` in the input with `uu_2` (escape the prefix itself).
2. If the string is a Python keyword, prefix it with a null byte (`\0`) so that step 2 transforms the first character.
3. If the first character is not in `[a-zA-Z]`, replace it with `u_{base62(codepoint)}`.
4. Replace every subsequent character not in `[a-zA-Z0-9_]` with `u_{base62(codepoint)}`.

URL path strings such as `/pets/{id}` are a single segment and are mangled in full - slashes, braces, and other characters all get escaped.

Common examples:

| Input | Result | Reason |
|---|---|---------------------|
| `for` | `u_0for` | keyword → `\0for`; `\0` (code point 0) → `u_0` |
| `/test/` | `u_ltestu_l` | `/` (cp 47) → `u_l` |
| `/pet/{petId}` | `u_lpetu_lu_1zpetIdu_21` | `/` `{` `}` all escaped |
| `application/json` | `applicationu_ljson` | `/` (cp 47) → `u_l` |
| `200` | `u_o00` | `2` (cp 50) → `u_o` |

A `x-lapidary-type-name` extension on a schema overrides the generated class name.

### anyOf / oneOf derived schemas

When distributing a parent schema's constraints into `anyOf` or `oneOf` items (see *allOf and (oneOf or anyOf)*), the merged sub-schemas may differ from the originals. A changed sub-schema must receive a new name - it is a distinct derived type, not the original. Assign synthetic names by index:

- `anyOf` items: `AnyOf0`, `AnyOf1`, ...
- `oneOf` items: `OneOf0`, `OneOf1`, ...
- Cartesian product of `anyOf` × `oneOf`: `AnyOneOf0`, `AnyOneOf1`, ...

A sub-schema that is unchanged after distribution keeps its original name.

### Parameter names

OpenAPI scopes parameter names to their location: a `query` parameter a `path` parameter may both be named `id` in the same operation.
Python function arguments share a single namespace, so in order to avoind naming conflicts each parameter shall be suffixed with a location
marker to make it unique:

| Location | Suffix |
|---|---|
| query | `_q` |
| path | `_p` |
| header | `_h` |
| cookie | `_c` |

A query parameter named `limit` becomes `limit_q`.

A `x-lapidary-name` extension on a parameter overrides the generated name entirely, without any suffix.

Suffixes are used instead of traditional Hungration notation prefixes to facilitate name completion in IDEs.

## References

1. https://spec.openapis.org/oas/v3.0.4.html - the OpenAPI specification.
1. https://www.learnjsonschema.com/2019-09/ - an extended explanation of JSON Schema keywords. Wrong version, but helpful in many aspects.
1. https://apis.guru/ - a directory of OpenAPI/swagger descriptions (not updated since 2024).
