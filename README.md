# utde

A collection of **ut**ility **de**corators to simplify
my life.


## Persist

Instead of recomputing an expensive function
annotate it with a generic_persist decorator.
This decorator allows you to specify:

    - key_or_fn: Either a string or a function
    that generates a string from the wrapped_fn args
    - load_fn: A function that is used to retrieve
    stored data from key
    - store_fn: A function that is used to store
    the results of the "expensive" function call so that
    it can be loaded next time instead

Example:

```python
from utde import generic_persist

cache = dict()

def key_fn(day_str):
    year, month, day = day_str.split("-")
    return f"{year}/{month}/{day}"

def load_fn(key):
    if key in cache:
        return cache[key]

def store_fn(x, key):
    cache[key] = x

@generic_persist(key_fn, load_fn, store_fn)
def wrapped_fn(x, day_str):
    print("Imagine an expensive operation")
    return x * 2
```

### Pandas (optional)

`pip install utde[pandas]`

There is a overloaded version for pandas that will load/store
using the pickle format. Then you only have to provide where
to load/store the file from/to.

WARNING: Only provide a key to a location you trust in, as
unpickling a pickle file may execute arbitrary code.

```python
import pandas as pd
from utde import persist_pd

@persist_pd(lambda year: f"yearly_report_{year}.pkl")
def yearly_report(year: str) -> pd.DataFrame:
    return pd.DataFrame(data={"year": [year], "profit": [42]})
```

## Timer

Although its a simple function to write I often reinvented the
wheel and wrote a function/decorator to track the execution time
of a function of interest. 

```python
from utde import timer
import time

@timer
def slow_fn():
    time.sleep(2)

slow_fn()
```

Output:
```bash
INFO: `slow_fn` ellapsed time: 2.000s
```

## Checks

Some decorators which can come in handy when working with
jupyter notebooks

### Dynamic type checking

Given a function with type annotations the decorator
`@check` will assert that the function is not called with
types incompatible with the function annotation.
Note that there is some performance overhead since the code
will be dynamicially passed to [beartype](https://beartype.readthedocs.io/en/latest/) which handles dynamic type checking.


```python
from utde import check

@check
def integer_sum(x: int, y:int):
    return x + y

integer_sum(10, 10)  # works
integer_sum(1.25, 2.5)  # raises an utde.errors.TypeCheckError
```

**Note:** I didn't use pydantic as it didn't complain when I tried to call
a function `foo(x: int)` with `foo(1.0)`. This might be a design decision
however I personally prefer stricter type checking here.

### Experemental: Linting

**Note:** Linting is currently only supported where the function
resides in a classical python file e.g. `foo.py`. I'm working
on making this feature available at least in jupyter notebooks

If not disabled via `@check(enable_lint_checks=False)`, @check
will check the fn code for linting errors and raise a `utde.errors.LintCheckError`
if [ruff](https://docs.astral.sh/ruff/linter/) detects an error that overlaps
with the function definition call.


This function will fail with an error:
```python
from utde import lint

@lint
def fn_with_unused_variable():
    unused_var = 42
```

however the following code will pass since
the function `fn_with_unused_variable` is not decorated
with `@lint`:

```python
from utde import lint

def fn_with_unused_variable():
    unused_var = 42

@lint
def super_clean_function():
    used_var = 10
    return used_var + 32
```
