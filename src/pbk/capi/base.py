import ctypes
import typing


class KernelOpaquePtr:
    """Base class for wrapping opaque C pointers from bitcoinkernel.

    This class provides memory management and lifetime handling for C objects
    exposed through the kernel API. It supports both owned pointers (which are
    automatically destroyed when the Python object is garbage collected) and
    unowned views (which are not destroyed).

    Subclasses should set `_create_fn` and `_destroy_fn` class attributes to
    enable direct instantiation and automatic cleanup.

    Attributes:
        _as_parameter_: The underlying ctypes pointer to the C object.
        _owns_ptr: If True, this object owns the pointer and will destroy it
            when garbage collected.
        _parent: Optional parent object that must be kept alive for the lifetime
            of this object to prevent premature destruction.
        _create_fn: Constructor function for creating new C objects. If None,
            the class cannot be instantiated directly.
        _destroy_fn: Destructor function for freeing C objects. If None,
            the object cannot be destroyed (view-only classes).
    """

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
        """Initialize a new kernel object by calling the underlying C constructor.

        The arguments are passed through to the subclass's `_create_fn`. The created
        pointer is owned by this instance and will be automatically destroyed when
        the object is garbage collected.

        Args:
            *args: Positional arguments forwarded to the C constructor function.
            **kwargs: Keyword arguments forwarded to the C constructor function.

        Raises:
            TypeError: If the class does not support direct instantiation (i.e.,
                `_create_fn` is None).
            RuntimeError: If the C constructor returns a null pointer, indicating
                instantiation failed due to invalid arguments or other errors.
        """
        if self._create_fn is None:
            raise TypeError(
                f"{self.__class__.__name__} cannot be instantiated directly. "
            )
        self._as_parameter_ = self._create_fn(*args, **kwargs)
        if not self._as_parameter_:
            raise RuntimeError(f"Failed to create {self.__class__.__name__}")
        self._owns_ptr = True

    @classmethod
    def _from_handle(cls, ptr):
        """Construct from an owned C pointer.

        This factory method wraps a C pointer that is owned by the returned Python
        object. The underlying C object will be automatically destroyed when the
        Python object is garbage collected.

        Args:
            ptr: A ctypes pointer to the C object.

        Returns:
            A new instance wrapping the owned pointer.

        Raises:
            ValueError: If the pointer is null, as propagated from `_from_ptr`.
        """
        return cls._from_ptr(ptr, owns_ptr=True)

    @classmethod
    def _from_view(cls, ptr, parent=None):
        """Construct from an unowned view of a C pointer.

        This factory method wraps a C pointer that is NOT owned by the returned
        Python object. The underlying C object will not be destroyed when the
        Python object is garbage collected. If a parent object is provided, it
        will be kept alive for the lifetime of the returned view to ensure the
        underlying C object remains valid.

        Args:
            ptr: A ctypes pointer to the C object.
            parent: Optional parent object to keep alive for the lifetime of
                this view. This ensures the underlying C object is not destroyed
                while the view exists.

        Returns:
            A new instance wrapping the unowned pointer.

        Raises:
            ValueError: If the pointer is null, as propagated from `_from_ptr`.
        """
        return cls._from_ptr(ptr, owns_ptr=False, parent=parent)

    @classmethod
    def _from_ptr(cls, ptr: ctypes.c_void_p, owns_ptr: bool = True, parent=None):
        """Wrap a C pointer with configurable ownership semantics.

        This is the low-level factory method used by `_from_handle` and `_from_view`.
        It creates a new instance without calling `__init__`, directly setting the
        internal pointer and ownership attributes.

        Args:
            ptr: A ctypes pointer to the C object.
            owns_ptr: If True, the returned instance owns the pointer and will
                destroy it when garbage collected. If False, the pointer is not
                destroyed (view semantics).
            parent: Optional parent object to keep alive for the lifetime of
                this instance.

        Returns:
            A new instance wrapping the pointer with the specified ownership.

        Raises:
            ValueError: If the pointer is null.
        """
        if not ptr:
            raise ValueError(f"Failed to create {cls.__name__}: pointer cannot be NULL")
        instance = cls.__new__(cls)
        instance._as_parameter_ = ptr
        instance._owns_ptr = owns_ptr
        instance._parent = parent
        return instance

    def __del__(self):
        """Clean up the underlying C object if owned.

        This destructor is called when the Python object is garbage collected.
        If this instance owns the pointer (`_owns_ptr` is True), it calls the
        `_destroy_fn` to free the underlying C object. If the pointer is not
        owned (view semantics), no cleanup is performed.

        Note:
            This method is not thread-safe. In practice, it should only be
            called from a single thread during garbage collection.

        Raises:
            RuntimeError: If this instance owns the pointer but `_destroy_fn`
                is not set, indicating a library bug that would cause memory
                leaks.
        """
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
        """Enter the context manager.

        Enables using this object with the `with` statement for automatic
        resource cleanup.

        Returns:
            self: The instance itself.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the context manager and clean up resources.

        This is called when exiting a `with` block. It delegates to `__del__`
        to ensure the underlying C object is destroyed if owned.

        Args:
            exc_type: The type of exception that occurred, or None.
            exc_value: The exception instance that occurred, or None.
            traceback: The traceback object, or None.

        Raises:
            RuntimeError: If the instance owns the pointer but `_destroy_fn`
                is not set, as propagated from `__del__`.
        """
        self.__del__()
