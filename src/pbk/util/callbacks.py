import pbk.capi.bindings as k
import pbk.util.type


def initialize_callbacks(interface_callbacks: k.Structure, user_data=None, **callbacks):
    # Store user_data
    interface_callbacks._user_data = pbk.util.type.UserData(user_data)
    interface_callbacks.user_data = interface_callbacks._user_data.c_void_p

    # Keep references to the C function pointers to prevent garbage collection
    interface_callbacks._callbacks = {}

    # Iterate over the fields in the struct
    for field_name, field_type in interface_callbacks._fields_:  # type: ignore
        if field_name == "user_data":
            continue

        cb_func = callbacks.pop(field_name)
        if cb_func is not None:
            # Wrap the Python function into a C function pointer
            c_callback = field_type(cb_func)  # type: ignore
            setattr(interface_callbacks, field_name, c_callback)
            # Keep reference to prevent garbage collection
            interface_callbacks._callbacks[field_name] = c_callback
        else:
            setattr(interface_callbacks.field_name, None)  # type: ignore

    unused_callbacks = callbacks.keys()
    if unused_callbacks:
        raise ValueError(f"Callbacks {unused_callbacks} are not recognized")
