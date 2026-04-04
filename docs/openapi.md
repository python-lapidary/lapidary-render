# OpenAPI

OpenAPI compatibility

- ✅ `openapi`: validated (3.0.* accepted)
- `info`
    - ❌ `license`: N/A; it's up to the user to verify the accepted use.
    - 🗓️ `title` and other fields: planned as part of project readme

- 🗓️ `externalDocs`: planned as part of the project readme
- ✅ `servers`: first server is used
    - ✅ `url`: used as the base URL
    - ✅ `variables`: default values are used to evaluate the server URL

- ✅ `security`: implemented
- ❌ `tags`: ignored
- `components`
    - ✅ `schemas`:
        - 🗓️ `title`: planned as part of class docstr
        - `type`
            - ✅ [no value]: implemented as `pydantic.JsonValue`
            - ✅ `object`: implemented as pydantic model
            - ✅ `array`: implemented as list
            - ✅ scalars: `string`, `integer`, `number`, `boolean`  converted to `str`, `int`, `float` and `bool`

        - ⚠️ `format`: Implemented for string types: `uuid`, `date`, `date-time`, `time` and `decimal`
        - ✅ assertion keywords: as supported by [annotated-types](https://github.com/annotated-types/annotated-types)
        - ✅ `allOf`: implemented
        - ✅ `anyOf`: implemented as union
        - ⚠️ `oneOf`: treated as `anyOf` and implemented as `Union`
        - 🗓️ `not`: planned
        - ✅ `required`: non-required properties are turned to `Union[None, $type]`
        - `additionalProperties`:
            - ✅ boolean: supported as pydantic `extra: 'allow'` or `'forbid'`
            - 🗓️ schema: planned as either a `Mapping` type or a `__pydantic_extra__` field

        - 🔍 `enum`: ignored; might be implemented for simple types as `Literal`
        - 📄 `description`: planned as part of docstr
        - ✅ `default`: if present, the property type turned to `Union[None, $type]` and has default value `None`
          - 🔍 caveat: default values are not to be sent between Web API client and server, instead they are implied by the receiving side. Lapidary could potentially implement generating default values for some cases but they don't necessary need to validate against the schema.
        - ✅ `nullable`: if true, the property type is turned to `Union[None, $type]`
        - ✅ `readOnly` & `writeOnly`: if either is true, the property type is turned to `Union[None, $type]` and has default value `None`; planned as part of docstr

               ⚠️ caveat: readOnly properties are only to be sent to API server, and writeOnly only to be received by the client. A property might be both required one way, and invalid the other way, which could not be directly represented in Python, except with two or three classes for every schema.

        - 📄 `discriminator`: planed for use with pydantic discriminated unions
        - 🔍 `example`: might be used as part of docstr
        - 🗓️ `externalDocs`: planned as part of docstr
        - 🗓️ `deprecated`: planned
        - ❌ `xml`: ignored, currently not planned

    - `responses`
        - 🗓️ `description`: planned as part of docstr
        - ✅ `headers`: if present, used as fields in the response envelope class
        - ✅ `content`: implemented; used as operation method return type, and a way to resolve model type for a response
        - 🔍 `links`: ignored; might be used to generate methods in the response envelope

    - ✅ `parameters`: used in-line in operations
    - 🔍 `examples`: currently ignored
    - `requestBodies`
        - 🗓️ `description`: planned as part of docstr
        - ✅ `content`: implemented
        - 🗓️ `required`: planned

    - ✅ `headers`: implemented
    - ⚠️ `securitySchemes`: implemented with httpx_auth
        - ❌ `refreshUrl`: not supported

    - 🗓️ `links`: planned
    - 🗓️ `callbacks`: only planning to generate models from referenced schemas

- `paths`:
    - 🗓️ by path: planned as keys in a TypedDict
    - ✅ by oprtationId: mapped to operation methods
        - ✅ `operationId`: used as method name
        - 🗓️ `summary`, `description`: planned as parts of docstr
        - ❌ `servers`: ignored
        - `parameters`
            - ✅ `name`: OpenAPI parameter names are not unique and might contain characters invalid for python names, therefore they're escaped and suffix-hungarian notation is used to distinguish between cookie, header, path and query parameters
            - ✅ `in`: implemented, suffix-hungarian notation is used to separate parameters
            - ✅ `required`: non-required parameters are optional with default value `None`
            - 🗓️ `deprecated`: planned
            - 🗓️ `allowEmptyValue`: planned
            - 🗓️ `content`: key: planned, value: processed as schema
            - ⚠️ `style`: partially implemented
            - 🗓️ `allowReserved`: planned
            - ✅ `schema`: implemented
            - 🔍 `example` & `examples`: considered
