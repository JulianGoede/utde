import logging
import pytest
import pydoc
from utde import timer
from unittest.mock import patch, MagicMock


@patch(
    "time.time", side_effect=[0, 10, 10]
)  # don't know why timer is called a 3rd time but the 3rd value is irrelevant
def test_timer_prints_ellapsed_function_time(time_mock: MagicMock, caplog):
    @timer
    def foo():
        pass

    foo()

    time_mock.assert_called()
    record_tuples = caplog.record_tuples
    assert len(caplog.messages) == 1
    assert len(record_tuples) == 1, f"Found record_tuples = {record_tuples}"
    [_, level, msg] = record_tuples[0]
    assert level == logging.INFO, f"Expected (default) loglevel INFO but got {level}"
    expected = "`foo` ellapsed time: 10.000s"
    assert msg == expected


@patch(
    "time.time", side_effect=[0, 2.1234567, 10]
)  # don't know why timer is called a 3rd time but the 3rd value is irrelevant
def test_timer_prints_desired_format(time_mock: MagicMock, caplog):
    @timer(time_fmt="%.7f")
    def foo():
        pass

    foo()

    time_mock.assert_called()
    record_tuples = caplog.record_tuples
    assert len(caplog.messages) == 1
    assert len(record_tuples) == 1, f"Found record_tuples = {record_tuples}"
    [_, level, msg] = record_tuples[0]
    assert level == logging.INFO, f"Expected (default) loglevel INFO but got {level}"
    expected = "`foo` ellapsed time: 2.1234567s"
    assert msg == expected


@pytest.mark.parametrize(
    "expected_loglevel",
    [(logging.DEBUG), (logging.INFO), (logging.WARN), (logging.ERROR)],
)
def test_timer_respects_loglevel(expected_loglevel, caplog):
    @timer(level=expected_loglevel)
    def foo():
        pass

    foo()

    record_tuples = caplog.record_tuples
    assert len(caplog.messages) == 1
    assert len(record_tuples) == 1, f"Found record_tuples = {record_tuples}"
    [_, level, _] = record_tuples[0]
    assert level == expected_loglevel


def test_timed_function_returns_correct_result():
    @timer
    def foo(a, b=5):
        return a + b

    actual = foo(37)
    expected = 42
    assert actual == expected


def test_timer_preserves_wrapped_fn_information():
    expected_doc = "The answer to all questions is 42"

    @timer
    def wrapped_fn():
        """
        The answer to all questions is 42
        """
        pass

    doc_string = pydoc.render_doc(wrapped_fn)
    doc_string = str(doc_string).strip()

    assert doc_string.endswith(expected_doc), "The doc of wrapped_fn was overwritten"
