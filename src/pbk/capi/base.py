import ctypes
import typing


def camel_to_snake(s):
    return "".join(["_" + c.lower() if c.isupper() else c for c in s]).lstrip("_")


class KernelOpaquePtr:
    _as_parameter_: ctypes.c_void_p | None = None  # Underlying ctypes object
    _owns_ptr: bool = True  # If True, user is responsible for freeing the pointer
    _parent = (
        None  # Parent object that must be kept alive for the lifetime of this object
    )
    _create_fn: typing.Callable | None = None  # If None, cannot be created directly
    _destroy_fn: typing.Callable | None = (
        None  # If None, cannot be destroyed. Should only be used for view-only classes.
    )

    def __init__(self, *args, **kwargs):
        if self._create_fn is None:
            raise TypeError(
                f"{self.__class__.__name__} cannot be instantiated directly. "
            )
        self._as_parameter_ = self._create_fn(*args, **kwargs)
        if not self._as_parameter_:
            raise RuntimeError(f"Failed to create {self.__class__.__name__}")
        self._owns_ptr = True

    @property
    def contents(self):
        assert self._as_parameter_
        return self._as_parameter_.contents  # type: ignore

    @classmethod
    def _from_handle(cls, ptr):
        """
        Construct from an owned handle. Will be destroyed at the end of its lifetime.
        """
        return cls._from_ptr(ptr, owns_ptr=True)

    @classmethod
    def _from_view(cls, ptr, parent=None):
        """
        Construct from an unowned view. Parent, if set, will be kept alive for lifetime of child.
        """
        return cls._from_ptr(ptr, owns_ptr=False, parent=parent)

    @classmethod
    def _from_ptr(cls, ptr: ctypes.c_void_p, owns_ptr: bool = True, parent=None):
        """Wrap a C pointer owned by the kernel."""
        if not ptr:
            raise ValueError(f"Failed to create {cls.__name__}: pointer cannot be NULL")
        instance = cls.__new__(cls)
        instance._as_parameter_ = ptr
        instance._owns_ptr = owns_ptr
        instance._parent = parent
        return instance

    def __del__(self):
        # In theory, this is not thread-safe. In practice, this should
        # never be reached from multiple threads.
        if self._as_parameter_ and self._owns_ptr:
            if not self._destroy_fn:
                raise RuntimeError(
                    f"{self.__class__.__name__} owns pointer but has no _destroy_fn set. "
                    "This is a library error that will leak memory. Please report the issue at "
                    "https://github.com/stickies-v/py-bitcoinkernel/issues."
                )
            self._destroy_fn(self)
            self._as_parameter_ = None  # type: ignore

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__del__()
