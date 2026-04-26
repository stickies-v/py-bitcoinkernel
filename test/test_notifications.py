import ctypes

import pytest

import pbk.notifications


NOTIFICATION_CALLBACK_NAMES = (
    "block_tip",
    "header_tip",
    "progress",
    "warning_set",
    "warning_unset",
    "flush_error",
    "fatal_error",
)


def _noop(*_args: object) -> None:
    pass


def test_notification_callbacks_empty() -> None:
    cb = pbk.notifications.NotificationInterfaceCallbacks()
    for name in NOTIFICATION_CALLBACK_NAMES:
        assert not bool(getattr(cb, name))


def test_notification_callbacks_single() -> None:
    cb = pbk.notifications.NotificationInterfaceCallbacks(warning_unset=_noop)
    assert bool(cb.warning_unset)
    for name in set(NOTIFICATION_CALLBACK_NAMES) - {"warning_unset"}:
        assert not bool(getattr(cb, name))


def test_notification_callbacks_unknown_raises() -> None:
    with pytest.raises(ValueError, match="not recognized"):
        pbk.notifications.NotificationInterfaceCallbacks(blok_tip=_noop)


def test_notification_callbacks_user_data_rejected() -> None:
    # user_data is reserved internal state, not a public callback kwarg.
    with pytest.raises(ValueError, match="not recognized"):
        pbk.notifications.NotificationInterfaceCallbacks(user_data=_noop)


def test_notification_callbacks_swallow_user_data() -> None:
    # The C trampoline receives `void* user_data` as its first arg. The
    # wrapper must discard it before calling the user's Python callback,
    # which sees only the domain-relevant args.
    seen: list[tuple[int, ctypes.c_ubyte]] = []
    cb = pbk.notifications.NotificationInterfaceCallbacks(
        warning_unset=lambda warning: seen.append((1, warning)),
    )
    # Invoke the C function pointer the way the kernel would: with a
    # user_data void* prepended to the domain args.
    cb.warning_unset(ctypes.c_void_p(), ctypes.c_ubyte(7))
    assert seen == [(1, 7)]
