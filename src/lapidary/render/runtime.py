from .model import python

_MODULE_RUNTIME = 'lapidary.runtime'

AnyJsonType = python.AnnotatedType(python.GenericType(python.NameRef(_MODULE_RUNTIME, 'AnyJSONValue')))
ModelBase = python.NameRef(_MODULE_RUNTIME, 'ModelBase')
