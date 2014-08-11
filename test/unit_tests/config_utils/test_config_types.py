# Copyright 2014 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the config types."""

from __future__ import unicode_literals
from __future__ import print_function

import unittest
import mock

from testfixtures import compare

from xylem.config_utils import Any
from xylem.config_utils import Boolean
from xylem.config_utils import String
from xylem.config_utils import Path
from xylem.config_utils import List
from xylem.config_utils import Dict
from xylem.config_utils import MergingDict
from xylem.config_utils import ConfigValueError
from xylem.config_utils import maybe_instantiate
from xylem.config_utils import expand_input_path
from xylem.config_utils import UNSET_YAML
from xylem.config_utils import UNSET_COMMAND_LINE

from xylem.text_utils import text_type


def same_pair(v):
    return (v, v)


class ConfigTypesTestCase(unittest.TestCase):

    def _test_type(self, type_, command_line, fail_command_line, yaml, fail_yaml, verify, fail_verify):

        t = maybe_instantiate(type_)

        # test unset value
        unset = t.unset_value()
        compare(unset, t.from_yaml(UNSET_YAML))
        compare(unset, t.from_command_line(UNSET_COMMAND_LINE))
        t.verify(unset)
        self.assertTrue(t.is_unset(unset))
        self.assertFalse(t.is_unset(not unset))

        # test command line multiple
        self.assertIsInstance(t.command_line_multiple(), bool)

        # test command_line_parsing_help
        self.assertIsInstance(t.command_line_parsing_help(), (type(None), text_type))

        # test merging
        compare(unset, t.merge(unset, unset))
        def verify_merge(input):
            compare(input, t.merge(input, unset))
            compare(input, t.merge(unset, input))

        # test parsing from command line
        for input, result in command_line:
            try:
                with mock.patch.object(t, 'verify', side_effect=t.verify) as verify_mock:
                    compare(result, t.from_command_line(input))
                    if result != unset:
                        self.assertGreaterEqual(verify_mock.call_count, 1)
                verify_merge(result)
            except ConfigValueError:
                print("from_command_line raised unexpected: `{}`".format(input))
                raise
        for input in fail_command_line:
            with self.assertRaises(ConfigValueError):
                result = t.from_command_line(input)
                print("from_command_line did not raise: `{}`; result: `{}`".format(input, result))

        # test parsing from yaml structure
        for input, result in yaml:
            try:
                with mock.patch.object(t, 'verify', side_effect=t.verify) as verify_mock:
                    compare(result, t.from_yaml(input))
                    if result != unset:
                        self.assertGreaterEqual(verify_mock.call_count, 1)
                verify_merge(result)
            except ConfigValueError:
                print("from_yaml raised unexpected: `{}`".format(input))
                raise
        for input in fail_yaml:
            with self.assertRaises(ConfigValueError):
                result = t.from_yaml(input)
                print("from_yaml did not raise: `{}`; result: `{}`".format(input, result))

        # test verification
        for input in verify:
            try:
                t.verify(input)
                verify_merge(input)
            except ConfigValueError:
                print("verify raised unexpected: `{}`".format(input))
                raise
        for input in fail_verify:
            with self.assertRaises(ConfigValueError):
                t.verify(input)
                print("verify did not raise: `{}`".format(input))

    def test_any(self):
        command_line = [
            same_pair("foo bar"),
            ("{foo: bar, quux: quax}", dict(foo="bar",quux="quax")),
            ("[1,2,3]", [1, 2, 3]),
            same_pair("1,2,3"),
            ("", None),
            same_pair(None),
        ]
        fail_command_line = [
            "foo: bar, quux: quax",
            "[ , [",
            "[}",
            "*&^%%&*(",
        ]
        yaml = [
            same_pair("foo"),
            same_pair([1, 2]),
            same_pair([[]]),
            same_pair({}),
            same_pair(None),
        ]
        fail_yaml = [
        ]
        verify = [
            False,
            True,
            None,
            [1,2],
            [1,[2, "foo"]],
            {},
            {"foo": "bar", 2: {3: 42}},
            3.141,
            "foobar",
        ]
        fail_verify = [
        ]
        self._test_type(Any, command_line, fail_command_line, yaml, fail_yaml, verify, fail_verify)

    def test_bool(self):
        command_line = [
            ("true", True),
            ("TRUE", True),
            ("yes", True),
            ("YES", True),
            ("false", False),
            ("FALSE", False),
            ("no", False),
            ("NO", False),
            ("", None),
            same_pair(None),
        ]
        fail_command_line = [
            "yEs",
            "nO",
            "truE",
            "faLse",
            "foo bar",
            "{foo: bar, quux: quax}",
            "[1,2,3]",
            "1,2,3",
            "foo: bar",
            "[ , [",
            "[}",
            "*&^%%&*(",
        ]
        yaml = [
            same_pair(None),
            same_pair(False),
            same_pair(True),
        ]
        fail_yaml = [
            [1,2],
            [1,[2, "foo"]],
            {},
            {"foo": "bar", 2: {3: 42}},
            3.141,
            "foobar",
        ]
        verify = [
            False,
            True,
            None,
        ]
        fail_verify = [
            [1,2],
            [1,[2, "foo"]],
            {},
            {"foo": "bar", 2: {3: 42}},
            3.141,
            "foobar",
        ]
        self._test_type(Boolean, command_line, fail_command_line, yaml, fail_yaml, verify, fail_verify)

    def test_string(self):
        command_line = [
            same_pair("foo"),
            same_pair("[foo,bar]"),
            same_pair("yes"),
            same_pair("FALSE"),
            same_pair("{foo: bar, quux: quax}"),
            same_pair("[1,2,3]"),
            same_pair("1,2,3"),
            same_pair("foo: bar"),
            same_pair("[ , ["),
            same_pair("[}"),
            same_pair("*&^%%&*("),
            same_pair("\n"),
            same_pair("   "),
            same_pair(""),
            same_pair(None),
        ]
        fail_command_line = [
        ]
        yaml = command_line
        fail_yaml = [
            ["foo", "bar"],
            True,
            [1,2],
            [1,[2, "foo"]],
            {},
            {"foo": "bar", 2: {3: 42}},
            3.141,
        ]
        verify = [x[0] for x in command_line]
        fail_verify = fail_yaml
        self._test_type(String, command_line, fail_command_line, yaml, fail_yaml, verify, fail_verify)

    def test_path(self):
        def expand_pair(path):
            return (path, expand_input_path(path))
        command_line = [
            expand_pair("~"),
            expand_pair("~/foo/bar"),
            expand_pair("/foo"),
            expand_pair("/foo/bar/"),
            expand_pair("/"),
            expand_pair("."),
            expand_pair(""),
            same_pair(None),
        ]
        fail_command_line = [
        ]
        yaml = command_line
        fail_yaml = [
            ["foo", "bar"],
            True,
            [1,2],
            [1,[2, "foo"]],
            {},
            {"foo": "bar", 2: {3: 42}},
            3.141,
        ]
        verify = [x[1] for x in command_line] + [x[1] for x in yaml]
        fail_verify = fail_yaml
        self._test_type(Path, command_line, fail_command_line, yaml, fail_yaml, verify, fail_verify)

    def test_list(self):
        command_line = [
            ("[1,2,3]", [1, 2, 3]),
            (["[1,2,3]", "4"], [1, 2, 3, 4]),
            ("{}, [], foo", [{}, [], "foo"]),
            ("1,2,3", [1, 2, 3]),
            ("foo: bar, quux: quax" ,[{"foo": "bar"}, {"quux": "quax"}]),
            ("{foo: bar, quux: quax}" ,[{"foo": "bar", "quux": "quax"}]),
            ("foo bar", ["foo bar"]),
            ("yes", [True]),
            ("", []),
            same_pair(None),
        ]
        fail_command_line = [
            "[ , [",
            "[}",
            "*&^%%&*(",
        ]
        yaml = [
            same_pair([1, 2]),
            same_pair([1, "foo"]),
            same_pair([[]]),
            same_pair(None),
        ]
        fail_yaml = [
            "foo",
            {},
            1,
            True,
        ]
        verify = [x[1] for x in command_line] + [x[1] for x in yaml]
        fail_verify = fail_yaml
        t = List()
        self._test_type(t, command_line, fail_command_line, yaml, fail_yaml, verify, fail_verify)
        compare([1,2], t.merge([1,2], [3,4]))
        compare([3,4], t.merge(None, [3,4]))
        compare([], t.merge([], [3,4]))

    def test_list_of_strings(self):
        command_line = [
            ("[foo bar, baz]", ["foo bar", "baz"]),
            (["", "foo", "bar,baz", "[]"], ["foo", "bar", "baz"]),
            ("foo bar", ["foo bar"]),
            ("", []),
            same_pair(None),
        ]
        fail_command_line = [
            "[1,2,3]",
            ["[1,2,3]", "4"],
            "{}, [], foo",
            "1,2,3",
            "foo: bar, quux: quax",
            "{foo: bar, quux: quax}",
            "yes",
            "[ , [",
            "[}",
            "*&^%%&*(",
        ]
        yaml = [
            same_pair(["foo", "bar"]),
            same_pair([]),
            same_pair(None),
        ]
        fail_yaml = [
            [1, "foo"],
# FIXME: we want the following to fail, but currently with the way unset works, it does not
#            [None],
            "foo",
            {},
            1,
            True,
        ]
        verify = [x[1] for x in command_line] + [x[1] for x in yaml]
        fail_verify = fail_yaml
        self._test_type(List(String()), command_line, fail_command_line, yaml, fail_yaml, verify, fail_verify)

    def test_dict(self):
        command_line = [
            ("foo: bar, quux: quax", {"foo": "bar", "quux": "quax"}),
            ("{foo: bar, quux: quax}", {"foo": "bar", "quux": "quax"}),
            ("foo: 2", {"foo": 2}),
            ("foo:", {"foo": None}),
            ("foo bar:", {"foo bar": None}),
            (["foo:", "", "bar: 2"], {"foo": None, "bar": 2}),
            ("", {}),
            same_pair(None),
        ]
        fail_command_line = [
            ["foo: 1", "foo: 2"],
            "{1:2}",
            "1,2,3",
            "[1,2,3]",
            "[ , [",
            "[}",
            "*&^%%&*(",
        ]
        yaml = [
            same_pair({"foo": "bar"}),
            same_pair({"foo": "bar", "baz": 2}),
            same_pair({}),
            same_pair(None),
        ]
        fail_yaml = [
            False,
            True,
            [1,2],
            [1,[2, "foo"]],
            {"foo": "bar", 2: {3: 42}},
            3.141,
            "foobar",
        ]
        verify = [x[1] for x in command_line] + [x[1] for x in yaml]
        fail_verify = fail_yaml
        t = Dict()
        self._test_type(t, command_line, fail_command_line, yaml, fail_yaml, verify, fail_verify)
        compare({"1": 2}, t.merge({"1": 2}, {"3": 4}))
        compare({"3": 4}, t.merge(None, {"3": 4}))
        compare({}, t.merge({}, {"3": 4}))

    def test_mergingdict_of_list_of_string(self):
        command_line = [
            ("foo: [bar, baz]", {"foo": ["bar", "baz"]}),
            ("foo: []", {"foo": []}),
            ("", {}),
            (None, {}),
        ]
        fail_command_line = [
            "{foo: bar, quux: quax}",
            ["foo: []", "foo: []"],
# FIXME: we want the following to fail, but currently with the way unset works, it does not
#            "foo:",
            "{1:2}",
            "1,2,3",
            "[1,2,3]",
            "[ , [",
            "[}",
            "*&^%%&*(",
        ]
        yaml = [
            same_pair({"foo": ["bar"]}),
            same_pair({"foo": ["bar"], "baz": []}),
            same_pair({}),
            (None, {}),
        ]
        fail_yaml = [
            {"foo": ["bar"], "baz": [2]},
            False,
            True,
            [1,2],
            [1,[2, "foo"]],
            {"foo": "bar", 2: {3: 42}},
            3.141,
            "foobar",
        ]
        verify = [x[1] for x in command_line] + [x[1] for x in yaml]
        fail_verify = fail_yaml
        t = MergingDict(List(String))
        self._test_type(t, command_line, fail_command_line, yaml, fail_yaml, verify, fail_verify)
        compare({"1": 2, "3": 4}, t.merge({"1": 2}, {"3": 4}))
        compare({"1": 2}, t.merge({"1": 2}, {}))
        compare({"3": 4}, t.merge({}, {"3": 4}))
