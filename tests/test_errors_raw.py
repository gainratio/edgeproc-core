"""Tests for the raw-failure duck-typing helpers.

These probe a failure of unknown shape: a thrown ``Exception``, an httpx/requests
response-like object with ``.status_code``, a fetch-style object with ``.status``,
a plain mapping, or a bare string.
"""

from __future__ import annotations

from types import SimpleNamespace

from edgeproc_core.errors import error_name_of, error_text_of, http_status_of


class PrivacyViolationError(Exception):
    """Stand-in for an egress-guard block, matched by class name."""


def test_should_read_status_from_mapping_when_present() -> None:
    # Given a fetch-style mapping raw
    # When the status is read
    # Then the numeric status is returned
    assert http_status_of({"status": 402}) == 402


def test_should_read_status_code_from_httpx_style_object() -> None:
    # Given an httpx/requests response-like object
    raw = SimpleNamespace(status_code=429)
    # When the status is read
    # Then the .status_code attribute is honoured
    assert http_status_of(raw) == 429


def test_should_return_none_when_status_is_non_numeric() -> None:
    # Given a raw whose status is a string
    # When the status is read
    # Then it is rejected as non-numeric
    assert http_status_of({"status": "402"}) is None


def test_should_return_none_when_status_is_boolean() -> None:
    # Given a raw whose status is a bool (an int subclass)
    # When the status is read
    # Then the bool is not mistaken for a status code
    assert http_status_of({"status": True}) is None


def test_should_return_none_when_no_status_present() -> None:
    # Given a raw with no status at all
    # When the status is read
    # Then None is returned
    assert http_status_of(Exception("boom")) is None


def test_should_use_exception_class_name_as_error_name() -> None:
    # Given a raised built-in exception
    # When its name is read
    # Then the class name is used
    assert error_name_of(TimeoutError("late")) == "TimeoutError"


def test_should_prefer_explicit_name_attribute_over_class_name() -> None:
    # Given a raw carrying an explicit .name (a JS-style error object)
    raw = SimpleNamespace(name="AbortError")
    # When its name is read
    # Then the explicit attribute wins
    assert error_name_of(raw) == "AbortError"


def test_should_return_empty_name_for_a_plain_string() -> None:
    # Given a bare string raw
    # When its name is read
    # Then there is no name
    assert error_name_of("boom") == ""


def test_should_return_string_raw_verbatim_as_text() -> None:
    # Given a bare string raw
    # When its text is read
    # Then the string is returned unchanged
    assert error_text_of("Failed to fetch") == "Failed to fetch"


def test_should_join_message_and_body_as_text() -> None:
    # Given a raw with both a message and a body
    raw = {"message": "boom", "body": "NetworkError when fetching"}
    # When its text is read
    # Then message and body are joined
    assert error_text_of(raw) == "boom NetworkError when fetching"


def test_should_use_exception_str_as_text_when_no_message_attribute() -> None:
    # Given a raised exception with no .message/.body attributes
    # When its text is read
    # Then the exception's str() is used
    assert error_text_of(ConnectionError("Connection refused")) == "Connection refused"


def test_should_read_status_from_a_nested_response() -> None:
    # Given an exception that carries its response, like requests.HTTPError
    raw = SimpleNamespace(response=SimpleNamespace(status_code=402))
    # When the status is read
    # Then the response's status is used
    assert http_status_of(raw) == 402


def test_should_read_status_attr_from_a_nested_response() -> None:
    # Given a wrapper whose response is fetch-style, with .status
    raw = SimpleNamespace(response=SimpleNamespace(status=503))
    # When the status is read
    # Then the response's .status is used
    assert http_status_of(raw) == 503


def test_should_read_status_from_a_nested_response_mapping() -> None:
    # Given a mapping that carries a response mapping
    # When the status is read
    # Then the nested mapping's status is used
    assert http_status_of({"response": {"status": 429}}) == 429


def test_should_return_none_when_nested_response_has_no_status() -> None:
    # Given a wrapper whose response carries no status
    raw = SimpleNamespace(response=SimpleNamespace(body="oops"))
    # When the status is read
    # Then None is returned
    assert http_status_of(raw) is None


def test_should_prefer_the_direct_status_over_a_nested_response() -> None:
    # Given a raw with its own status and a different one on its response
    raw = SimpleNamespace(status_code=429, response=SimpleNamespace(status_code=500))
    # When the status is read
    # Then the direct status wins
    assert http_status_of(raw) == 429


def test_should_not_loop_when_response_points_at_itself() -> None:
    # Given a raw whose response is itself
    raw = SimpleNamespace()
    raw.response = raw
    # When the status is read
    # Then it terminates with None
    assert http_status_of(raw) is None


def test_should_not_loop_when_two_responses_point_at_each_other() -> None:
    # Given two raws whose responses form a cycle
    first, second = SimpleNamespace(), SimpleNamespace()
    first.response, second.response = second, first
    # When the status is read
    # Then it terminates with None
    assert http_status_of(first) is None
