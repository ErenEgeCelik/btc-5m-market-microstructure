"""Sanitized reference implementations of the models described in ``docs/``.

These modules take numbers and return numbers. There is no venue client, no
credential handling, and no order-submission or cancellation path anywhere in
this package -- see ``SECURITY.md`` for why that is a structural choice rather
than a disabled feature.
"""

__all__ = ["accounting", "clean_index", "ev_chain", "fair", "queue", "quote_model"]
