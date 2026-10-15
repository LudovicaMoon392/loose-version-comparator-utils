# loose-version-comparator-utils

Compares version strings that do not follow any strict spec by splitting on non-numeric boundaries.

```python
from loose_version_comparator_utils import LooseVersion, compare_versions, version_key

assert compare_versions("1.10", "1.9") == 1
assert compare_versions("1.0rc1", "1.0") == 1

versions = ["1.10", "1.2", "1.1", "1.0.1"]
assert sorted(versions, key=version_key) == ["1.0.1", "1.1", "1.2", "1.10"]

assert LooseVersion("1.0") < "1.1"
```

## Why this exists

Real-world version strings rarely obey SemVer. Packages ship tags like
`1.0rc2`, `2.5.0-beta.3`, or `v1.2`. Strict parsers reject these or order
them inconsistently. This library gives them a single, predictable ordering.

The trade-off: there is no special handling for prerelease semantics beyond
the natural sort order. `alpha` < `beta` < `rc` because of their letters, not
because of a hardcoded precedence table. If your ecosystem uses prerelease
tags that do not sort alphabetically the way you want, this library will not
fix that — pick a stricter tool.

## The awkward edge

When one version is a prefix of another (`1.0` vs `1.0.1`), the shorter one is
treated as though it had an empty string in the missing slot. Empty strings
sort before any real token, so `1.0` is less than `1.0.1`. This is deliberate;
it keeps the rule set small and the behaviour inspectable.
