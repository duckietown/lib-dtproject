from dtproject.constants import DEFAULT_DOCKER_REGISTRY, DUCKIETOWN
from dtproject.types import LayerBase

from . import get_project_path, skip_if_code_mounted, base_layer

from dtproject import DTProject
import unittest


class TestLayerBase(unittest.TestCase):

    def test_layer_base_project_v1(self):
        pd = get_project_path("basic_v1")
        p = DTProject(pd)
        # base info is not exposed in dtproject v1
        with self.assertRaises(NotImplementedError):
            _ = p.base_info

    def test_layer_base_project_v2(self):
        pd = get_project_path("basic_v2")
        p = DTProject(pd)
        # base info is not exposed in dtproject v1
        with self.assertRaises(NotImplementedError):
            _ = p.base_info

    def test_layer_base_project_v3(self):
        pd = get_project_path("basic_v3")
        p = DTProject(pd)
        # base info is not exposed in dtproject v1
        with self.assertRaises(NotImplementedError):
            _ = p.base_info

    def test_layer_base_project_v4(self):
        pd = get_project_path("basic_v4")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.base_info.repository, "dt-commons")
        self.assertEqual(p.base_info.registry, DEFAULT_DOCKER_REGISTRY)
        self.assertEqual(p.base_info.organization, DUCKIETOWN)
        self.assertEqual(p.base_info.tag, None)

    @skip_if_code_mounted
    def test_layer_base_project_v4_staging_registry(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        base: LayerBase = LayerBase(
            repository="my-repository",
            registry="staging-registry.io",
        )
        with base_layer(pname, base):
            p = DTProject(pd)
            # ---
            self.assertEqual(p.layers.base.repository, base.repository)
            self.assertEqual(p.layers.base.registry, base.registry)

    @skip_if_code_mounted
    def test_layer_base_project_v4_staging_registry(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        base: LayerBase = LayerBase(
            repository="my-repository",
            registry="example.com",
        )
        with base_layer(pname, base):
            p = DTProject(pd)
            # ---
            self.assertEqual(p.layers.base.repository, base.repository)
            self.assertEqual(p.layers.base.registry, base.registry)

    @skip_if_code_mounted
    def test_layer_base_project_v4_custom_organization(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        base: LayerBase = LayerBase(
            repository="my-repository",
            organization="best-organization-ever",
        )
        with base_layer(pname, base):
            p = DTProject(pd)
            # ---
            self.assertEqual(p.layers.base.repository, base.repository)
            self.assertEqual(p.layers.base.organization, base.organization)

    @skip_if_code_mounted
    def test_layer_base_project_v4_custom_tag(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        base: LayerBase = LayerBase(
            repository="my-repository",
            tag="best-tag-ever",
        )
        with base_layer(pname, base):
            p = DTProject(pd)
            # ---
            self.assertEqual(p.layers.base.repository, base.repository)
            self.assertEqual(p.layers.base.tag, base.tag)
