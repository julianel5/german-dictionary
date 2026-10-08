"""Pydantic DTOs (API contracts). Independent from domain dataclasses."""

from __future__ import annotations

import warnings

# `register` is a required dictionary field name but also an attribute of
# pydantic's BaseModel; the shadowing warning would be pure noise here.
warnings.filterwarnings(
    "ignore",
    message=r"Field name .* shadows an attribute in parent",
    category=UserWarning,
)
