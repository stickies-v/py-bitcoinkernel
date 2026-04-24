import typing

import pbk.capi.bindings as k
import pbk.util.type


def _initialize_callbacks(
    interface_callbacks: k.Structure,
    user_data: typing.Any = None,
    **callbacks: typing.Any,
) -> None:
    """
    Internal helper to wrap `user_data` and `callbacks` into ctypes,
    preventing garbage collection issues.

    This function is not thread-safe.
    """
    # Store user_data
    interface_callbacks._user_data = pbk.util.type.UserData(user_data)
    interface_callbacks.user_data = interface_callbacks._user_data._as_parameter_

    # Keep references to the C function pointers to prevent garbage collection
    interface_callbacks._callbacks = {}

    reserved = {"user_data", "user_data_destroy"}
    valid_fields = {name for name, _ in interface_callbacks._fields_} - reserved  # type: ignore
    unknown_callbacks = set(callbacks) - valid_fields
    if unknown_callbacks:
        raise ValueError(f"Callbacks {unknown_callbacks} are not recognized")

    # Iterate over the fields in the struct
    for field_name, field_type in interface_callbacks._fields_:  # type: ignore
        if field_name in reserved:
            continue

        cb_func = callbacks.get(field_name)
        if cb_func is None:
            continue
        # Wrap the Python function into a C function pointer
        c_callback = field_type(cb_func)
        setattr(interface_callbacks, field_name, c_callback)
        # Keep reference to prevent garbage collection
        interface_callbacks._callbacks[field_name] = c_callback
