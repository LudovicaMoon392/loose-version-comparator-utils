"""
Core implementation for loose version comparison.

Design choice: versions are split into tokens on every non-digit boundary,
producing an alternating list of integer/string tokens. Comparison then
pairs tokens position-by-position:
  - int vs int: numeric comparison
  - str vs str: ASCII (case-sensitive) comparison, *longer string is greater*
  - mixed types: strings sort before integers (matches the common
    convention that a prerelease tag like 'rc' precedes the next numeric bump)
  - different lengths: when one side runs out of tokens, the missing value
    is treated as an empty string. Because an empty string sorts before any
    real token, '1.0' is less than '1.0.1'.

Non-numeric, non-alphabetic characters ('.', '-', '_', '+') act purely as
separators and are discarded. The lexer never produces empty tokens.
"""

import functools
import re


class LooseVersion:
    """A parsed loose version string supporting rich comparisons."""

    __slots__ = ("_raw", "_tokens")

    def __init__(self, version: str) -> None:
        """Initialize and parse the version string.

        Args:
            version: The raw version string to parse. An empty string is
                permitted and represents the minimal version (no tokens).
        """
        if not isinstance(version, str):
            raise TypeError(f"version must be str, got {type(version).__name__}")
        self._raw = version
        self._tokens = _tokenize(version)

    @property
    def raw(self) -> str:
        """Return the original unparsed version string."""
        return self._raw

    @property
    def tokens(self) -> tuple:
        """Return the parsed token sequence as an immutable tuple."""
        return self._tokens

    @classmethod
    def _ensure(cls, other) -> "LooseVersion":
        """Coerce a comparand to a LooseVersion, raising TypeError if impossible."""
        if isinstance(other, LooseVersion):
            return other
        if isinstance(other, str):
            return cls(other)
        return NotImplemented  # type: ignore[return-value]

    def _cmp_key(self) -> tuple:
        """Return a tuple of (is_string, value) pairs for total ordering.

        Each token contributes a two-element sub-tuple so that strings and
        integers are never directly compared (which would raise TypeError in
        Python 3). For string tokens we also append the raw string so that a
        longer string compares greater than a shorter prefix.
        """
        key_parts = []
        for tok in self._tokens:
            if isinstance(tok, int):
                key_parts.append((1, tok))
            else:
                key_parts.append((0, tok))
        return tuple(key_parts)

    def __lt__(self, other) -> bool:
        o = self._ensure(other)
        if o is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return self._cmp_key() < o._cmp_key()

    def __le__(self, other) -> bool:
        o = self._ensure(other)
        if o is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return self._cmp_key() <= o._cmp_key()

    def __gt__(self, other) -> bool:
        o = self._ensure(other)
        if o is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return self._cmp_key() > o._cmp_key()

    def __ge__(self, other) -> bool:
        o = self._ensure(other)
        if o is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return self._cmp_key() >= o._cmp_key()

    def __eq__(self, other) -> bool:  # type: ignore[override]
        o = self._ensure(other)
        if o is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return self._cmp_key() == o._cmp_key()

    def __ne__(self, other) -> bool:  # type: ignore[override]
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented  # type: ignore[return-value]
        return not result

    def __hash__(self) -> int:
        return hash(self._cmp_key())

    def __repr__(self) -> str:
        return f"LooseVersion({self._raw!r})"

    def __str__(self) -> str:
        return self._raw


def _tokenize(version: str) -> tuple:
    """Split *version* into an alternating tuple of int and str tokens.

    Digits are grouped greedily into integers; alphabetic runs become strings.
    Separators (anything not a digit or letter) are discarded entirely, so
    the token stream never contains empty strings.
    """
    if not version:
        return ()
    tokens = []
    for chunk in re.split(r"[^0-9A-Za-z]+", version):
        if not chunk:
            continue
        if chunk.isdigit():
            tokens.append(int(chunk))
        else:
            # Greedily split into numeric and alphabetic runs so that a
            # hybrid like 'rc2' becomes ('rc', 2) rather than one opaque
            # string. The trailing/leading non-alpha fragments are preserved.
            start = 0
            for i in range(1, len(chunk)):
                prev_alpha = chunk[i - 1].isalpha()
                curr_alpha = chunk[i].isalpha()
                if prev_alpha != curr_alpha:
                    frag = chunk[start:i]
                    tokens.append(int(frag) if frag.isdigit() else frag)
                    start = i
            frag = chunk[start:]
            tokens.append(int(frag) if frag.isdigit() else frag)
    return tuple(tokens)


@functools.total_ordering
class _VersionKey:
    """A lightweight wrapper exposing total ordering over a token tuple."""

    __slots__ = ("_tokens",)

    def __init__(self, tokens: tuple) -> None:
        self._tokens = tokens

    def __eq__(self, other) -> bool:
        if not isinstance(other, _VersionKey):
            return NotImplemented
        return _compare_token_tuples(self._tokens, other._tokens) == 0

    def __lt__(self, other) -> bool:
        if not isinstance(other, _VersionKey):
            return NotImplemented
        return _compare_token_tuples(self._tokens, other._tokens) < 0

    def __hash__(self) -> int:
        return hash(self._tokens)


def _compare_token_tuples(a: tuple, b: tuple) -> int:
    """Compare two raw token tuples element-by-element.

    Mixed int/str comparisons are resolved by treating strings as less than
    integers. For string-vs-string we compare lexicographically, then by
    length so that longer strings win (e.g. 'beta' > 'bet').
    """
    for i in range(max(len(a), len(b))):
        ta = a[i] if i < len(a) else ""
        tb = b[i] if i < len(b) else ""
        if ta == tb:
            continue
        a_is_int = isinstance(ta, int)
        b_is_int = isinstance(tb, int)
        if a_is_int and b_is_int:
            return -1 if ta < tb else 1
        if a_is_int and not b_is_int:
            return 1
        if not a_is_int and b_is_int:
            return -1
        # Both strings
        if ta < tb:
            return -1
        if ta > tb:
            return 1
        if len(ta) < len(tb):
            return -1
        if len(ta) > len(tb):
            return 1
    return 0


def version_key(version: str) -> _VersionKey:
    """Return a totally-ordered key for *version*.

    This is useful for passing to ``sorted`` or ``heapq`` as a ``key=``
    argument without constructing a full LooseVersion wrapper.
    """
    return _VersionKey(_tokenize(version))


def compare_versions(a: str, b: str) -> int:
    """Compare two loose version strings.

    Returns -1 if *a* < *b*, 0 if equal, 1 if *a* > *b*.
    """
    return _compare_token_tuples(_tokenize(a), _tokenize(b))
