import typing

import pbk.capi.bindings as k


def _strip_user_data(fn: typing.Callable[..., None]) -> typing.Callable[..., None]:
    def wrapper(_user_data: typing.Any, *args: typing.Any) -> None:
        fn(*args)

    return wrapper


def _initialize_callbacks(
    interface_callbacks: k.Structure,
    **callbacks: typing.Any,
) -> None:
    """
    Internal helper to wrap `callbacks` into ctypes,
    preventing garbage collection issues.

    This function is not thread-safe.
    """
    interface_callbacks._callbacks = {}

    reserved = {"user_data", "user_data_destroy"}
    valid_fields = {name for name, _ in interface_callbacks._fields_} - reserved  # type: ignore
    unknown_callbacks = set(callbacks) - valid_fields
    if unknown_callbacks:
        raise ValueError(f"Callbacks {unknown_callbacks} are not recognized")

    for field_name, field_type in interface_callbacks._fields_:  # type: ignore
        if field_name in reserved:
            continue
        cb_func = callbacks.get(field_name)
        if cb_func is None:
            continue
        c_callback = field_type(_strip_user_data(cb_func))
        setattr(interface_callbacks, field_name, c_callback)
        interface_callbacks._callbacks[field_name] = c_callback
