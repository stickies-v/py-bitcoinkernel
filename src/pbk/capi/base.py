import ctypes

import pbk.capi.bindings


def camel_to_snake(s):
    return "".join(["_" + c.lower() if c.isupper() else c for c in s]).lstrip("_")


class KernelPtr:
    _as_parameter_: ctypes.c_void_p | None = None  # Underlying ctypes object
    _owns_ptr: bool = True  # If True, user is responsible for freeing the pointer

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("KernelPtr cannot be instantiated directly")

    @property
    def contents(self):
        assert self._as_parameter_
        return self._as_parameter_.contents  # type: ignore

    @classmethod
    def _from_ptr(cls, ptr: ctypes.c_void_p, owns_ptr: bool = True):
        """Wrap a C pointer owned by the kernel."""
        if not ptr:
            raise ValueError(f"Failed to create {cls.__name__}: pointer cannot be NULL")
        instance = cls.__new__(cls)
        instance._as_parameter_ = ptr
        instance._owns_ptr = owns_ptr
        return instance

    def __del__(self):
        if self._as_parameter_ and self._owns_ptr:
            self._destroy()
            self._as_parameter_ = None  # type: ignore

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.__del__()

    @property
    def kernel_name(self):
        snake_name = camel_to_snake(type(self).__name__)
        return f"kernel_{snake_name}"

    def _auto_kernel_fn(self, suffix: str, *args, **kwargs):
        fn_name = f"{self.kernel_name}_{suffix}"
        if hasattr(pbk.capi.bindings, fn_name):
            return getattr(pbk.capi.bindings, fn_name)(*args, **kwargs)

        raise NotImplementedError(f"'{fn_name}' does not exists")

    def _create(self, *args, **kwargs):
        return self._auto_kernel_fn("create", *args, **kwargs)

    def _destroy(self):
        self._auto_kernel_fn("destroy", self)


class KernelOpaquePtr(KernelPtr):
    def __init__(self, *args, **kwargs):
        self._as_parameter_ = self._create(*args, **kwargs)
        if not self._as_parameter_:
            raise RuntimeError(f"Failed to create {self.__class__.__name__}")
        self._owns_ptr = True

    @property
    def contents(self):
        raise NotImplementedError(
            "KernelOpaquePtr is an opaque pointer and its contents cannot be accessed directly"
        )
