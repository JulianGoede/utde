import time
import logging
from functools import partial, wraps


def _setup_logger(level):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


LOGGER = _setup_logger(logging.DEBUG)


def timer(fn=None, level=logging.INFO, time_fmt="%.3f"):
    if fn is None:
        return partial(timer, level=level, time_fmt=time_fmt)
    msg = "`%s` ellapsed time: " + time_fmt + "s"

    @wraps(fn)
    def apply_timed_fn(*args, **kwargs):
        start = time.time()
        result = fn(*args, **kwargs)
        expired_seconds: float = time.time() - start
        LOGGER.log(level, msg, fn.__name__, expired_seconds)
        return result

    return apply_timed_fn
