import yaml

from lapidary.render.model import openapi, python

with open('operation_functions.yaml') as doc_file:
    doc = yaml.safe_load(doc_file)
model = openapi.OpenApiModel.model_validate(doc)


module_path = python.ModulePath('lapidary_test')
union_str_absent = python.GenericTypeHint.union_of(
    (python.TypeHint.from_type(str), python.TypeHint.from_str('lapidary.runtime.absent:Absent'))
)
common_attributes = [
    python.AttributeModel(
        name='a',
        annotation=python.AttributeAnnotationModel(
            type=union_str_absent,
            field_props={},
            default='lapidary.runtime.absent.ABSENT',
        ),
    ),
    python.AttributeModel(
        name='b',
        annotation=python.AttributeAnnotationModel(
            type=union_str_absent,
            field_props={},
            default='lapidary.runtime.absent.ABSENT',
        ),
    ),
]
