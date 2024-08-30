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
from utde.persist import generic_persist

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
from utde.persist import persist_pd

@persist_pd(lambda year: f"yearly_report_{year}.pkl")
def yearly_report(year: str) -> pd.DataFrame:
    return pd.DataFrame(data={"year": [year], "profit": [42]})
```

## Timer

Although its a simple function to write I often reinvented the
wheel and wrote a function/decorator to track the execution time
of a function of interest. 

```python
from utde.profiling import timer
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
