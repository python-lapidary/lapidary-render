import builtins
import keyword
import logging
import re
from typing import cast

logger = logging.getLogger(__name__)

VALID_IDENTIFIER_RE = re.compile(r'^[a-zA-Z]\w*$', re.ASCII)


def check_name(name: str, check_builtins=True) -> None:
    if (
        name is None
        or keyword.iskeyword(name)
        or (check_builtins and name in builtins.__dict__)
        or not VALID_IDENTIFIER_RE.match(name)
    ):
        raise ValueError('Invalid identifier', name)


def _escape_char(s: str) -> str:
    return f'u_{ord(s):06x}'


def escape_name(name: str) -> str:
    name = name.replace('u_', 'u' + _escape_char('_'))
    return re.sub('[^a-zA-Z]', lambda match: _escape_char(cast(str, match.group())), name[0]) + re.sub(
        '[^a-zA-Z0-9_]', lambda match: _escape_char(cast(str, match.group())), name[1:]
    )


def maybe_mangle_name(name: str) -> str:
    """
    Names that are Python keywords or in builtins get suffixed with an underscore (_).
    Names that are not valid Python identifiers or start with underscore are mangled by replacing invalid characters
    with u_{code}.
    Since 'u_' is the escaping prefix, it also gets replaced
    """
    if name is None or name == '':
        raise ValueError()

    if keyword.iskeyword(name):
        name = '\0' + name
    if not VALID_IDENTIFIER_RE.match(name) or 'u_' in name:
        return escape_name(name)
    else:
        return name
