"""Reusable test fakes (spies) for use-case integration tests."""

from __future__ import annotations


class FakeUseCase:
    """Generic fake use-case with spy tracking.

    Supports configurable response and optional error injection.

    Usage::

        fake = FakeUseCase(response=MyResponseDTO(...))
        result = fake.execute(some_request)
        assert fake.call_count == 1
        assert fake.last_request is some_request
    """

    def __init__(self, response=None, error: Exception | None = None):
        self.last_request = None
        self.call_count = 0
        self._response = response
        self._error = error

    def execute(self, request):
        """Record the call and return the configured response (or raise)."""
        self.last_request = request
        self.call_count += 1
        if self._error:
            raise self._error
        return self._response

    def reset(self):
        """Clear recorded calls so the fake can be reused."""
        self.last_request = None
        self.call_count = 0
