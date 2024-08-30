import pytest
import tempfile
import pydoc
from utde import generic_persist
from utde.persist import FEATURE_PANDAS
from unittest.mock import Mock
from inspect import signature
from pathlib import Path


def LOAD_FN_NO_ARG(key):
    return None


def STORE_FN_NO_ARG(result, key):
    return None


def KEY_FN_NO_ARG():
    return "foo"


def KEY_FN_X_ARG(x):
    return f"x={x}"


def KEY_FN_Y_ARG(y):
    return f"y={y}"


def KEY_FN_X_ARG_Y_DEFAULT(x, y=7):
    return f"x={x}; y={y}"


def WRAPPED_FN_X_ARG(x):
    return x


def WRAPPED_FN_X_Y_ARG(x, y):
    return x + y


def WRAPPED_FN_X_ARG_Y_DEFAULT(x, y=42):
    return x + y


@pytest.mark.parametrize(
    "_test_description, key_fn, wrapped_fn, args, expected_calling_signature",
    [
        (
            "key_fn must not receive args from wrapped_fn if not defined in the signature of key_fn",
            KEY_FN_NO_ARG,
            WRAPPED_FN_X_Y_ARG,
            {"args": [39, 3], "kwargs": dict()},
            {},
        ),
        (
            "key_fn must not receive kwargs from wrapped_fn if not defined in the signature of key_fn",
            KEY_FN_NO_ARG,
            WRAPPED_FN_X_Y_ARG,
            {"args": [], "kwargs": {"x": 39, "y": 3}},
            {},
        ),
        (
            "key_fn must receive positional argument `y` from wrapped_fn",
            KEY_FN_Y_ARG,
            WRAPPED_FN_X_Y_ARG,
            {"args": [0, 42], "kwargs": dict()},
            {"y": 42},
        ),
        (
            "key_fn must receive kwarg `y` from wrapped_fn",
            KEY_FN_Y_ARG,
            WRAPPED_FN_X_Y_ARG,
            {"args": [0], "kwargs": {"y": 42}},
            {"y": 42},
        ),
        (
            "key_fn must receive arguments `(x, y)` from wrapped_fn",
            KEY_FN_X_ARG_Y_DEFAULT,
            WRAPPED_FN_X_Y_ARG,
            {"args": [0], "kwargs": {"y": 42}},
            {"x": 0, "y": 42},
        ),
        (
            "key_fn must receive default argument y from wrapped_fn",
            KEY_FN_X_ARG_Y_DEFAULT,
            WRAPPED_FN_X_ARG_Y_DEFAULT,
            {"args": [7], "kwargs": dict()},
            {"x": 7, "y": 42},
        ),
        (
            "key_fn default argument y must be overwritten by default argument y from wrapped_fn",
            KEY_FN_X_ARG_Y_DEFAULT,
            WRAPPED_FN_X_ARG_Y_DEFAULT,
            {"args": [7], "kwargs": dict()},
            {"x": 7, "y": 42},
        ),
        (
            "key_fn default argument y must not be set if wrapped_fn does not specify it",
            KEY_FN_X_ARG_Y_DEFAULT,
            WRAPPED_FN_X_ARG,
            {"args": [7], "kwargs": dict()},
            {"x": 7},
        ),
    ],
)
def test_key_fn_receives_arguments_of_wrapped_fn(
    _test_description, key_fn, wrapped_fn, args, expected_calling_signature
):
    mocked_key_fn = Mock(wraps=key_fn)
    mocked_key_fn.__signature__ = signature(
        key_fn
    )  # this is a workaround as Mock changes fn signature and this is used to retrieve passed args/kwargs

    persist = generic_persist(mocked_key_fn, LOAD_FN_NO_ARG, STORE_FN_NO_ARG)
    persist_wrapped_fn = persist(wrapped_fn)

    _ = persist_wrapped_fn(*args["args"], **args["kwargs"])
    mocked_key_fn.assert_called_once_with(**expected_calling_signature)


@pytest.mark.parametrize(
    "load_fn, wrapped_fn_call_expected", [(lambda s: s, False), (lambda s: None, True)]
)
def test_wrapped_fn_executed_iff_load_fn_returns_non_none_result(
    load_fn, wrapped_fn_call_expected
):
    persist = generic_persist("foo", load_fn, STORE_FN_NO_ARG)

    def wrapped_fn():
        pass

    mocked_wrapped_fn = Mock(wraps=wrapped_fn)
    persist_wrapped_fn = persist(mocked_wrapped_fn)
    _ = persist_wrapped_fn()

    if wrapped_fn_call_expected:
        mocked_wrapped_fn.assert_called_once()
    else:
        mocked_wrapped_fn.assert_not_called()


def test_wrapped_fn_result_is_stored_at_specified_key():
    x = 42
    key = "foo"
    cache = dict()

    def store_fn(x, key):
        cache[key] = x

    persist = generic_persist(key, LOAD_FN_NO_ARG, store_fn)
    persist_wrapped_fn = persist(WRAPPED_FN_X_ARG)

    assert (
        key not in cache
    ), f"key {key} must not be present in cache before it is written to"
    persist_wrapped_fn(x)
    assert key in cache, f"key {key} wasn't stored in cache"
    assert x == cache[key], f"store_fn didn't store value {x} at {key} but {cache[key]}"


# SECTION: TEST BY EXAMPLES
# HERE I WANT TO PROVIDE SOME EXAMPLES
# BOTH TO SHOW HOW TO USE THIS FUNCTION
# AS WELL AS TO HAVE "REALISTIC" test cases


def test_simple_caching_use_case():
    cache = dict()

    def key_fn(day_str):
        year, month, day = day_str.split("-")
        return f"{year}/{month}/{day}"

    def load_fn(key):
        if key in cache:
            return cache[key]

    def store_fn(x, key):
        cache[key] = x

    persist = generic_persist(key_fn, load_fn, store_fn)

    @persist
    def wrapped_fn(x, day_str):
        print("Imagine an expensive operation")
        return x * 2

    x = 21
    day = "2024-08-26"
    key = key_fn(day)
    assert key not in cache, "cache must not be filled yet"
    computed_result = wrapped_fn(x, day)
    assert computed_result == 42
    assert cache[key] == computed_result, "cache must store the computed result"

    cached_result = wrapped_fn(x + 2, day)
    assert cache[key] == cached_result, "somehow result was computed and not cached .."

    # invalidated cache
    cache.pop(key)
    new_result = wrapped_fn(x + 2, day)
    assert new_result == 46, "wrapped function wasn't recomputed"
    assert cache[key] == new_result, "somehow result was computed and not cached .."


def test_persist_preserves_wrapped_fn_information():
    expected_doc = "The answer to all questions is 42"

    @generic_persist(KEY_FN_NO_ARG, LOAD_FN_NO_ARG, STORE_FN_NO_ARG)
    def wrapped_fn():
        """
        The answer to all questions is 42
        """
        pass

    doc_string = pydoc.render_doc(wrapped_fn)
    doc_string = str(doc_string).strip()

    assert doc_string.endswith(expected_doc), "The doc of wrapped_fn was overwritten"


@pytest.mark.skipif(not FEATURE_PANDAS, reason="feature requires pandas")
def test_persist_pd():
    import pandas as pd
    from utde.persist import persist_pd

    with tempfile.TemporaryDirectory() as tmpdir:
        year = "2024"
        wrapped_counter = Mock()

        def key_fn(year: str):
            return f"{tmpdir.rstrip('/')}/report_{year}.pkl"

        @persist_pd(key_fn)
        def yearly_report(year: str, wrapped_counter=wrapped_counter) -> pd.DataFrame:
            wrapped_counter(year)
            return pd.DataFrame(data={"year": [year], "profit": [42]})

        expected_filename = f"{tmpdir.rstrip('/')}/report_{year}.pkl"
        assert not Path(
            expected_filename
        ).is_file(), f"Pickle file {expected_filename} must not exist before"

        _ = yearly_report(year)

        assert Path(
            expected_filename
        ).is_file(), f"Pickle file {expected_filename} must exist after"

        _ = yearly_report(year)
        wrapped_counter.assert_called_once_with(year)
