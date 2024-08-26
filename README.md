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

