import unittest

from loose_version_comparator_utils import (
    LooseVersion,
    compare_versions,
    version_key,
)


class TestCompareVersions(unittest.TestCase):
    def test_simple_numeric(self):
        self.assertEqual(compare_versions("1.0", "1.0"), 0)
        self.assertEqual(compare_versions("1.0", "2.0"), -1)
        self.assertEqual(compare_versions("2.0", "1.0"), 1)

    def test_unequal_length(self):
        self.assertEqual(compare_versions("1.0", "1.0.1"), -1)
        self.assertEqual(compare_versions("1.0.1", "1.0"), 1)
        self.assertEqual(compare_versions("1", "1.0.0.0"), -1)

    def test_double_digit_segments(self):
        self.assertEqual(compare_versions("1.10", "1.9"), 1)
        self.assertEqual(compare_versions("1.10.1", "1.9.9"), 1)

    def test_pre_release_string(self):
        # a present string token sorts after an empty (missing) slot
        self.assertEqual(compare_versions("1.0rc1", "1.0"), 1)
        self.assertEqual(compare_versions("1.0rc1", "1.0rc2"), -1)
        self.assertEqual(compare_versions("1.0rc2", "1.0rc10"), -1)

    def test_string_longer_is_greater(self):
        # 'beta' > 'bet' because the longer string wins on ties
        self.assertEqual(compare_versions("1.0beta", "1.0bet"), 1)
        self.assertEqual(compare_versions("1.0bet", "1.0beta"), -1)

    def test_mixed_separators(self):
        # separators are discarded, so '1.0-0' == '1_0+0'
        self.assertEqual(compare_versions("1.0-0", "1_0+0"), 0)
        self.assertEqual(compare_versions("1.0-0", "1.0.0"), 0)

    def test_empty_string(self):
        self.assertEqual(compare_versions("", ""), 0)
        self.assertEqual(compare_versions("", "1"), -1)
        self.assertEqual(compare_versions("1", ""), 1)

    def test_no_separator(self):
        self.assertEqual(compare_versions("v1", "v2"), -1)
        self.assertEqual(compare_versions("v2", "v1"), 1)

    def test_precedence_stable(self):
        # 'rc1' vs 'rc10' — numeric comparison inside the tag
        self.assertEqual(compare_versions("2.0rc1", "2.0rc10"), -1)


class TestLooseVersion(unittest.TestCase):
    def test_equality_and_inequality(self):
        self.assertEqual(LooseVersion("1.0"), LooseVersion("1.0"))
        self.assertNotEqual(LooseVersion("1.0"), LooseVersion("1.1"))

    def test_rich_comparisons(self):
        self.assertLess(LooseVersion("1.0"), LooseVersion("1.1"))
        self.assertLessEqual(LooseVersion("1.0"), LooseVersion("1.0"))
        self.assertGreater(LooseVersion("1.1"), LooseVersion("1.0"))
        self.assertGreaterEqual(LooseVersion("1.0"), LooseVersion("1.0"))

    def test_comparison_with_str(self):
        self.assertLess(LooseVersion("1.0"), "1.1")
        self.assertGreater(LooseVersion("1.1"), "1.0")
        self.assertEqual(LooseVersion("1.0"), "1.0")

    def test_invalid_type_raises(self):
        with self.assertRaises(TypeError):
            LooseVersion(123)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            LooseVersion("1.0") < 123  # type: ignore[operator]

    def test_properties(self):
        v = LooseVersion("1.0rc2")
        self.assertEqual(v.raw, "1.0rc2")
        self.assertEqual(v.tokens, (1, 0, "rc", 2))

    def test_repr_and_str(self):
        v = LooseVersion("1.0")
        self.assertEqual(repr(v), "LooseVersion('1.0')")
        self.assertEqual(str(v), "1.0")

    def test_hashable(self):
        a = LooseVersion("1.0")
        b = LooseVersion("1.0")
        self.assertEqual(hash(a), hash(b))
        self.assertEqual(len({a, b}), 1)

    def test_sortable_list(self):
        versions = ["1.10", "1.2", "1.1", "1.0.1"]
        sorted_versions = sorted([LooseVersion(v) for v in versions])
        self.assertEqual([str(v) for v in sorted_versions], ["1.0.1", "1.1", "1.2", "1.10"])


class TestVersionKey(unittest.TestCase):
    def test_key_function_sorts(self):
        versions = ["1.10", "1.2", "1.1", "1.0.1"]
        result = sorted(versions, key=version_key)
        self.assertEqual(result, ["1.0.1", "1.1", "1.2", "1.10"])

    def test_key_equality(self):
        self.assertEqual(version_key("1.0.0"), version_key("1.0.0"))
        self.assertNotEqual(version_key("1.0.0"), version_key("1.0.1"))

    def test_key_hashable(self):
        self.assertEqual(hash(version_key("1.0")), hash(version_key("1.0")))


if __name__ == "__main__":
    unittest.main()
