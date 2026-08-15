"""Service package with lightweight lazy convenience exports."""


def initialize_session_state() -> None:
    from .twin_service import initialize_session_state as _impl

    _impl()


def reset_demo() -> None:
    from .twin_service import reset_demo as _impl

    _impl()


__all__ = ["initialize_session_state", "reset_demo"]
