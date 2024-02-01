from black import Mode, NothingChanged, TargetVersion, format_file_contents


def format_code(code: str, strict: bool, is_pyi: bool) -> str:
    try:
        return format_file_contents(
            src_contents=code,
            fast=not strict,
            mode=Mode(
                target_versions={TargetVersion.PY38},
                is_pyi=is_pyi,
            ),
        )
    except NothingChanged:
        return code
