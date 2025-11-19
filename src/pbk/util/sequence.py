import abc
import collections.abc
import typing

T = typing.TypeVar("T")


class LazySequence(collections.abc.Sequence, typing.Generic[T], abc.ABC):
    """A lazy sequence that fetches items on-demand, e.g. from a C API.

    Implements the Sequence protocol for efficient access to arrays
    exposed by e.g. C APIs. Length is queried lazily, items are fetched
    on access.

    Subclasses must implement:
    - __len__(): Return the length of the sequence
    - _get_item(index): Get the item at the given index (0-based, non-negative)

    Subclasses should manage their own lifetime/ownership concerns.

    Optional caching pattern for expensive length operations:
        def __len__(self) -> int:
            if not hasattr(self, '_cached_len'):
                self._cached_len = compute_expensive_length()
            return self._cached_len
    """

    @abc.abstractmethod
    def __len__(self) -> int:
        """Return the length of the sequence.

        This method should be overridden by subclasses. Consider caching
        the result if computing the length is expensive.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def _get_item(self, index: int) -> T:
        """Get the item at the given index.

        Args:
            index: Non-negative index (already normalized from negative indexing)

        Returns:
            The item at the given index
        """
        raise NotImplementedError

    @typing.overload
    def __getitem__(self, index: int) -> T:
        """Get item at integer index."""
        ...

    @typing.overload
    def __getitem__(self, index: slice) -> "typing.Sequence[T]":
        """Get items at slice indices."""
        ...

    def __getitem__(self, index: int | slice) -> "T | typing.Sequence[T]":
        """Get item(s) at index. Supports negative indexing and slicing."""
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]

        if index < 0:
            index += len(self)

        if not (0 <= index < len(self)):
            raise IndexError("sequence index out of range")

        return self._get_item(index)

    def __repr__(self) -> str:
        """Return a string representation of the sequence."""
        return f"<{self.__class__.__name__} len={len(self)}>"
