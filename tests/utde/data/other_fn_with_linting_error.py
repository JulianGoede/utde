from utde import lint


@lint
def good_function():
    """
    This function contains
    no typing or linting errors
    """
    return 42


def unchecked_bad_function():
    unused_var = 42
