from .model import python

_MODULE_RUNTIME = 'lapidary.runtime'

JsonValue = python.AnnotatedType(python.NameRef(_MODULE_RUNTIME, 'JSONValue'))
ModelBase = python.NameRef(_MODULE_RUNTIME, 'ModelBase')
