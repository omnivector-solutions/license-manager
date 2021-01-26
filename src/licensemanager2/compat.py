"""
Definitions required for compatibility with other Python versions
"""

try:
    from typing import TypedDict  # type: ignore
except ImportError:  # pragma: nocover
    from typing_extensions import TypedDict


__all__ = ["TypedDict"]
