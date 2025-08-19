from dtproject.constants import DEFAULT_DOCKER_REGISTRY, DUCKIETOWN
from dtproject.exceptions import InconsistentDTProject
from dtproject.types import LayerBase, LayerOptions

from . import get_project_path, skip_if_code_mounted, custom_layer, base_layer, options_layer

from dtproject import DTProject
import unittest


class TestLayerOptions(unittest.TestCase):

    def test_layer_base_project_v1(self):
        pd = get_project_path("basic_v1")
        p = DTProject(pd)
        # we expect default options
        self.assertEqual(p.options, LayerOptions())

    def test_layer_base_project_v2(self):
        pd = get_project_path("basic_v2")
        p = DTProject(pd)
        # we expect default options
        self.assertEqual(p.options, LayerOptions())

    def test_layer_base_project_v3(self):
        pd = get_project_path("basic_v3")
        p = DTProject(pd)
        # we expect default options
        self.assertEqual(p.options, LayerOptions())

    def test_layer_base_project_v4(self):
        pd = get_project_path("basic_v4")
        p = DTProject(pd)
        # we expect default options
        self.assertEqual(p.options, LayerOptions())

    @skip_if_code_mounted
    def test_layer_base_project_v4_custom_options(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        options: LayerOptions = LayerOptions(
            needs_recipe=True
        )
        with options_layer(pname, options):
            # if we don't provide a recipe, we get an InconsistentDTProject exception
            with self.assertRaises(InconsistentDTProject):
                _ = DTProject(pd)
