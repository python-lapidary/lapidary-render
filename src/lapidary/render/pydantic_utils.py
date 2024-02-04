import typing

T = typing.TypeVar('T')


def find_annotation_optional(
    metadata: list,
    annotation_type: type[T],
) -> T | None:
    annos = [anno for anno in metadata if isinstance(anno, annotation_type)]
    if len(annos) > 1:
        raise TypeError(f'Multiple {annotation_type} annotations')
    return annos[0] if annos else None
