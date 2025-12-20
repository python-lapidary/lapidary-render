from .model import python

JsonValue = python.AnnotatedType(python.NameRef('pydantic', 'JsonValue'))
JsonObject = python.AnnotatedType(python.NameRef('builtins', 'dict'), (python.AnnotatedType.from_type(str), JsonValue))
ModelBase = python.NameRef('lapidary.runtime', 'ModelBase')
