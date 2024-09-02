import beartype
from functools import wraps, partial
from utde.errors import CheckError, TypeCheckError
from typing import Any


def check(fn=None, enable_type_checks=True):
    """
    Dynamically run a series of checks on function definition/call

    Keyword arguments:
    fn -- the function to be checked
    enable_type_checks -- when set to False skip running type checks
    """
    if fn is None:
        return partial(
            check,
            enable_type_checks=enable_type_checks,
        )

    @wraps(fn)
    def checked_fn(*args, **kwargs) -> Any | CheckError:
        checked_fn = fn
        if enable_type_checks:
            checked_fn = beartype.beartype(fn)
        try:
            return checked_fn(*args, **kwargs)
        except beartype.roar.BeartypeException as e:
            raise TypeCheckError(e)

    return checked_fn
