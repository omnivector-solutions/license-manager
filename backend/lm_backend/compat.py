_integrity_exceptions = []
try:
    from asyncpg.exceptions import IntegrityConstraintViolationError

    _integrity_exceptions.append(IntegrityConstraintViolationError)
except ImportError:  # pragma: nocover
    "asyncpg not installed"


try:
    from aiosqlite import IntegrityError

    _integrity_exceptions.append(IntegrityError)
except ImportError:  # pragma: nocover
    "aiosqlite not installed"


INTEGRITY_CHECK_EXCEPTIONS = tuple(_integrity_exceptions)
