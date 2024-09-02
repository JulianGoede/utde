import beartype
import inspect
import os
import logging
from subprocess import CompletedProcess, run
from functools import wraps, partial
from typing import Any, Callable
from utde.errors import CheckError, TypeCheckError, LintCheckError

LOGGER = logging.getLogger()


def _code_overlaps_lint_message(
    abs_file_name: str, lint_msg: str, code_start: int, code_end: int
) -> bool:
    assert lint_msg is not None, "lint_msg must not be None"
    assert len(lint_msg) > 0, "lint_msg must contain information"
    linting_errors = lint_msg.split("\n")
    for linting_error in linting_errors:
        error_parts = linting_error.split(":")
        if len(error_parts) < 3:
            continue  # ignore lines not conforming file:line:col: message
        file = error_parts[0]
        assert (
            error_parts[1].isdigit()
        ), f"linenumber of linting error must be an int but got {error_parts[1]}"
        line: int = int(error_parts[1])
        same_file: bool = str(os.path.relpath(abs_file_name)) == file
        same_lines: bool = code_start <= line and line < code_end
        if same_file and same_lines:
            return True
    return False


def _get_fn_range(fn: Callable) -> tuple[int, int]:
    _, starting_fn_line = inspect.findsource(fn)
    fn_code_str = inspect.getsource(fn)
    fn_len = fn_code_str.count(os.linesep)
    code_start: int = starting_fn_line + 1
    code_end: int = code_start + fn_len
    return code_start, code_end


def lint_code(fn: Callable):
    """
    Run linter ruff over python file containing function
    and raise a LintCheckError if linter finds issues which
    arise inside the function definition.

    Arguments:
        fn -- the function to be linted
    """
    try:
        file_name = inspect.getfile(fn)
        assert file_name.endswith((".py", ".ipynb"))
    except Exception:
        LOGGER.warning(
            "WARNING: Skip linting `%s` as source file `%s` doesn't match '*.py' or '*.ipynb'",
            fn.__name__,
            file_name,
        )
        return
    lint_cmd: list[str] = ["ruff", "check", file_name, "--output-format=concise"]
    completed_process: CompletedProcess = run(lint_cmd, capture_output=True)
    if completed_process.returncode != 0:
        error_msg = str(completed_process.stdout, encoding="utf-8")
        code_start, code_end = _get_fn_range(fn)
        if _code_overlaps_lint_message(file_name, error_msg, code_start, code_end):
            raise LintCheckError(error_msg)


def check(fn=None, enable_type_checks=True, enable_lint_checks=True):
    """
    Dynamically run a series of checks on function definition/call

    Keyword arguments:
    fn -- the function to be checked
    enable_type_checks -- when set to False skip running type checks
    enable_lint_checks -- when set to False skip running linter
    """
    if fn is None:
        return partial(
            check,
            enable_type_checks=enable_type_checks,
            enable_lint_checks=enable_lint_checks,
        )

    if enable_lint_checks:
        lint_code(fn)

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
