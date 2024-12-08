import keyword
import logging
import re
from typing import cast

import base62

logger = logging.getLogger(__name__)

RE_REPL_FIRST = re.compile('[^a-zA-Z]')
RE_REPL_NEXT = re.compile('[^a-zA-Z0-9_]')


def _escape_char(s: str) -> str:
    return f'u_{base62.encode(ord(s))}'


def _repl(match: re.Match) -> str:
    return _escape_char(cast(str, match.group()))


def escape_name(name: str) -> str:
    name = name.replace('u_', 'u' + _escape_char('_'))
    return RE_REPL_FIRST.sub(_repl, name[0]) + RE_REPL_NEXT.sub(_repl, name[1:])


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
    return escape_name(name)
