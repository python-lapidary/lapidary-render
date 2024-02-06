def encode_json_pointer(path: str) -> str:
    return path.replace('~', '~0').replace('/', '~1')


def decode_json_pointer(encoded: str) -> str:
    return encoded.replace('~1', '/').replace('~0', '~')
