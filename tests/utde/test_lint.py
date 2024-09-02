import pytest
from utde.errors import LintCheckError
from utde.lint import lint


def test_check_fails_on_linting_error():
    with pytest.raises(LintCheckError):
        # had to put this code into a seperate file
        # so the project linter doesn't complain
        # about the linting error ^^
        import data.fn_with_linting_error

        _ = data.fn_with_linting_error


def test_check_succeeds_if_linter_fails_elsewhere():
    # had to put this code into a seperate file
    # so the project linter doesn't complain
    # about the linting error ^^
    import data.other_fn_with_linting_error

    _ = data.other_fn_with_linting_error


def test_check_succeeds_on_surpressed_linting():
    @lint
    def foo():
        unused_var = 42  # noqa


def test_check_linting_disabled_if_inside_python_repl():
    code = ["from utde import check", "@lint", "def foo():", "\tunused_var=42"]
    code = "\n".join(code)
    exec(code)
