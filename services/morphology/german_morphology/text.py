"""Text normalization shared by lookup indexing, search and morphology."""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")


def normalize(surface: str) -> str:
    """Normalize a German word/surface string for indexing and lookup.

    Steps: Unicode NFC, strip + collapse internal whitespace, lowercase
    (``str.lower``, which preserves ``ß``). Umlauts are preserved as-is;
    ``ä``/``ö``/``ü`` are *not* decomposed into ``ae``/``oe``/``ue``.
    """
    text = unicodedata.normalize("NFC", surface)
    text = _WHITESPACE.sub(" ", text.strip())
    return text.lower()
