# ruff: noqa: D101,D105

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, MutableMapping
from typing import Any, TypeVar

# Define type variables for keys and values
KT = TypeVar("KT")
VT = TypeVar("VT")


class AttrDict[KT, VT](MutableMapping[KT, VT]):
    def __init__(self, *args: Mapping[KT, VT] | Iterable[tuple[KT, VT]], **kwargs: Any):
        self._data: dict[KT, VT] = {}
        self.update(dict(*args, **kwargs))

    def __setitem__(self, key: KT, value: VT) -> None:
        self._data[key] = self._convert(value)

    def __getitem__(self, key: KT) -> VT:
        return self._data[key]

    def __delitem__(self, key: KT) -> None:
        del self._data[key]

    def __iter__(self) -> Iterator[KT]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"AttrDict({self._data})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AttrDict):
            return self._data == other._data
        return self._data == other if isinstance(other, dict) else False

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]  # type: ignore
        except KeyError as e:
            msg = f"'AttrDict' object has no attribute '{name}'"
            raise AttributeError(msg) from e

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_data":
            super().__setattr__(name, value)
        else:
            self[name] = value  # type: ignore

    def __dir__(self) -> list[str]:
        return list(set(super().__dir__()) | {str(k) for k in self._data})

    def __or__(self, other: Mapping[KT, VT] | Iterable[tuple[KT, VT]] | None) -> AttrDict[KT, VT]:
        """Implement the | operator for AttrDict with nested merging."""
        if other is None:
            return self.copy()

        result = self.copy()
        other_dict = dict(other)

        for key, value in other_dict.items():
            if (
                key in result
                and isinstance(result[key], AttrDict)
                and isinstance(value, dict | AttrDict)
            ):
                result[key] |= AttrDict(value)  # type: ignore
            else:
                result[key] = self._convert(value)

        return result

    def __ror__(self, other: Mapping[KT, VT] | Iterable[tuple[KT, VT]] | None) -> AttrDict[KT, VT]:
        """Implement reverse | operator for AttrDict with nested merging."""
        return self.copy() if other is None else AttrDict(other) | self

    @classmethod
    def _convert(cls, value: Any) -> Any:
        if isinstance(value, Mapping) and not isinstance(value, AttrDict):
            return cls(value)
        return [cls._convert(v) for v in value] if isinstance(value, list) else value

    def to_dict(self) -> dict[KT, Any]:
        """Convert AttrDict to a regular dictionary recursively."""

        def _to_dict(value: Any) -> Any:
            if isinstance(value, AttrDict):
                return value.to_dict()
            return [_to_dict(v) for v in value] if isinstance(value, list) else value

        return {k: _to_dict(v) for k, v in self._data.items()}

    def copy(self) -> AttrDict[KT, VT]:
        """Return a shallow copy of the AttrDict."""
        return AttrDict(self._data)

    def deep_copy(self) -> AttrDict[KT, VT]:
        """Return a deep copy of the AttrDict."""
        from copy import deepcopy

        return AttrDict(deepcopy(self._data))

    def update(self, *args: Mapping[KT, VT] | Iterable[tuple[KT, VT]], **kwargs: Any) -> None:  # type: ignore
        """Update the AttrDict with the key/value pairs from other, overwriting existing keys."""
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    def setdefault(self, key: KT, default: VT | None = None) -> VT:
        """Insert key with a value of default if key is not in the dictionary."""
        if key not in self:
            self[key] = default  # type: ignore
        return self[key]

    def get(self, key: KT, default: Any = None) -> Any:
        """Return the value for key if key is in the dictionary, else default."""
        return self._data.get(key, default)

    def pop(self, key: KT, default: Any = None) -> Any:
        """Remove specified key and return the corresponding value."""
        return self._data.pop(key, default)

    def __contains__(self, key: object) -> bool:
        return key in self._data
