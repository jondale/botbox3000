"""Element abstractions for type comparisons without circular imports

.. versionadded:: 1.2"""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..elements._svg import SvgDocumentElement


class BaseElementProtocol(Protocol):
    """Abstraction for BaseElement, to be used as typehint in mixin classes"""

    def get_id(self, as_url=0) -> str:
        """Returns the element ID. If not set, generates a unique ID."""
        ...

    @property
    def root(self) -> "SvgDocumentElement":
        """Returns the element's root."""
        ...
