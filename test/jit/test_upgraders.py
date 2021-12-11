# Owner(s): ["oncall: jit"]

import io
import os
import sys
import torch

# Make the helper files in test/ importable
pytorch_test_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(pytorch_test_dir)
from torch.testing._internal.jit_utils import JitTestCase

if __name__ == '__main__':
    raise RuntimeError("This test file is not meant to be run directly, use:\n\n"
                       "\tpython test/test_jit.py TESTNAME\n\n"
                       "instead.")

class TestUpgraders(JitTestCase):
    def test_populated_upgrader_graph(self):
        @torch.jit.script
        def f():
            return 0

        buffer = io.BytesIO()
        torch.jit.save(f, buffer)
        buffer.seek(0)
        torch.jit.load(buffer)
        upgraders_size = torch._C._get_upgraders_map_size()
        upgraders_dump = torch._C._dump_upgraders_map()
        # make sure we only populate the upgrader map only once
        # so we load it again and make sure the upgrader map has
        # same content
        buffer.seek(0)
        torch.jit.load(buffer)
        upgraders_size_second_time = torch._C._get_upgraders_map_size()
        upgraders_dump_second_time = torch._C._dump_upgraders_map()
        self.assertTrue(upgraders_size == upgraders_size_second_time)
        self.assertTrue(upgraders_dump == upgraders_dump_second_time)

    def test_add_value_to_version_map(self):
        map_before_test = torch._C._get_operator_version_map()

        upgrader_bumped_version = 3
        upgrader_name = "_test_serialization_subcmul_0_2"
        upgrader_schema = "aten::_test_serialization_subcmul(Tensor self, Tensor other, Scalar alpha=2) -> Tensor"
        dummy_entry = torch._C._UpgraderEntry(upgrader_bumped_version, upgrader_name, upgrader_schema)

        torch._C._test_only_add_entry_to_op_version_map("aten::_test_serialization_subcmul", dummy_entry)
        map_after_test = torch._C._get_operator_version_map()
        self.assertTrue("aten::_test_serialization_subcmul" in map_after_test)
        self.assertTrue(len(map_after_test) - len(map_before_test) == 1)
        torch._C._test_only_remove_entry_to_op_version_map("aten::_test_serialization_subcmul")
        map_after_remove_test = torch._C._get_operator_version_map()
        self.assertTrue("aten::_test_serialization_subcmul" not in map_after_remove_test)
        self.assertEqual(len(map_after_remove_test), len(map_before_test))

    def test_populated_test_upgrader_graph(self):
        @torch.jit.script
        def f():
            return 0

        buffer = io.BytesIO()
        torch.jit.save(f, buffer)
        buffer.seek(0)
        torch.jit.load(buffer)

        # upgrader map should have populated now
        upgraders_size = torch._C._get_upgraders_map_size()

        test_map = {"a": "b", "c": "d"}
        torch._C._test_only_populate_upgraders(test_map)
        upgraders_size_after_test = torch._C._get_upgraders_map_size()
        self.assertEqual(upgraders_size_after_test - upgraders_size, 2)
        upgraders_dump = torch._C._dump_upgraders_map()
        self.assertTrue("a" in upgraders_dump)
        self.assertTrue("c" in upgraders_dump)

        torch._C._test_only_remove_upgraders(test_map)
        upgraders_size_after_remove_test = torch._C._get_upgraders_map_size()
        self.assertTrue(upgraders_size_after_remove_test == upgraders_size)
        upgraders_dump_after_remove_test = torch._C._dump_upgraders_map()
        self.assertTrue("a" not in upgraders_dump_after_remove_test)
        self.assertTrue("c" not in upgraders_dump_after_remove_test)
