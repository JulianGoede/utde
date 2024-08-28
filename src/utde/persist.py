import importlib
import inspect
from typing import Callable, Union, Any, Optional
from functools import wraps

FEATURE_PANDAS: bool = importlib.util.find_spec("pandas") is not None


def generic_persist(
    key_or_fn: Union[str, Callable[Any, str]] = None,
    load_fn: Callable[str, Union[Any, None]] = None,
    store_fn: Callable[Any, str] = None,
):
    """
    Try to load persisted data from provided (s3) key.
    Otherwise apply function and store results to specified key.

    Keyword arguments:
    key_or_fn -- either a string or a function
                 accepting the arguments of the `original` function and returns
                 a possibly parametrized string.
    load_fn   -- a function retrieving data from specified key
    store_fn  -- a function that persists computed output at specified key
    """

    def apply(fn_to_persist: Callable[Any, Any]) -> Any:
        assert (
            key_or_fn is not None
        ), "Must provide a key_or_fn (str or function->str) to persist data but got None"

        assert (
            load_fn is not None
        ), f"Must provide a load_fn (function(str)) to load data at {key_or_fn} but got None"

        assert (
            store_fn is not None
        ), f"Must provide a store_fn (function(Any, str)) to persist data (of type Any) at {key_or_fn} but got None"

        @wraps(fn_to_persist)
        def apply_with_persist(*args, **kwargs):
            key_name = None
            if isinstance(key_or_fn, str):
                key_name = key_or_fn
            else:
                # convert *args, **kwargs + defaults from fn to keyword arguments
                # that belong to the key_or_fn signature and pass each matching kwarg
                # e.g. foo(x, y=42) => key_or_fn(y, z=69) will be called with key_or_fn(y=42)
                call_args = inspect.getcallargs(fn_to_persist, *args, **kwargs)
                key_or_fn_signature: inspect.Signature = inspect.signature(key_or_fn)
                key_or_fn_params = key_or_fn_signature.parameters.keys()
                key_fn_args = dict(
                    (k, v) for (k, v) in call_args.items() if k in key_or_fn_params
                )
                key_name = key_or_fn(**key_fn_args)
            persisted_data = load_fn(key_name)
            if persisted_data is not None:
                # print(f"DEBUG: SKIP - Found existing data at {key_name}")
                return persisted_data

            result = fn_to_persist(*args, **kwargs)
            store_fn(result, key_name)
            return result

        return apply_with_persist

    return apply


if FEATURE_PANDAS:
    import pandas as pd

    def persist_pd(key_or_fn: Union[str, Callable[Any, str]] = None):
        """
        Persist a pandas dataframe returned from the wrapped function.
        The dataframe is stored and loaded using pandas pickle format.

        WARNING: Only provide keys to locations you trust as unpickling
        a pickle file may execute arbitrary code.

        Keyword arguments:
        key_or_fn -- either a string or a function
                     accepting the arguments of the `original` function and returns
                     a possibly parametrized string.
        """

        def read_pd_pickle_optional(s) -> Optional[pd.DataFrame]:
            try:
                return pd.read_pickle(s)
            except Exception:
                return None

        def store_pd_pickle(df, s):
            df.to_pickle(s)

        return generic_persist(
            key_or_fn=key_or_fn,
            load_fn=read_pd_pickle_optional,
            store_fn=store_pd_pickle,
        )
