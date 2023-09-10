from typing import Dict

from dtproject.constants import DUCKIETOWN, DEFAULT_DOCKER_REGISTRY
from dtproject.types import Recipe

from . import get_project_path, custom_layer, skip_if_code_mounted

from dtproject import DTProject
import unittest


class TestLayers(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_layers_project_v1(self):
        pd = get_project_path("basic_v1")
        p = DTProject(pd)
        # ---
        with self.assertRaises(NotImplementedError):
            _ = p.layers

    def test_layers_project_v2(self):
        pd = get_project_path("basic_v2")
        p = DTProject(pd)
        # ---
        with self.assertRaises(NotImplementedError):
            _ = p.layers

    def test_layers_project_v3(self):
        pd = get_project_path("basic_v3")
        p = DTProject(pd)
        # ---
        with self.assertRaises(NotImplementedError):
            _ = p.layers

    def test_layers_project_v4(self):
        pd = get_project_path("basic_v4")
        p = DTProject(pd)
        # ---
        self.assertEqual(set(p.layers.as_dict().keys()), set(DTProject.KNOWN_LAYERS))

    @skip_if_code_mounted
    def test_custom_layers(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        layers: Dict[str, dict] = {
            "web": {"keywords": ["fun", "games"], "url": "example.com"},
            "contributors": {"developers": ["qui", "quo"], "testers": ["qua"]},
        }
        with custom_layer(pname, "web", layers["web"]):
            with custom_layer(pname, "contributors", layers["contributors"]):
                p = DTProject(pd)
                # ---
                self.assertEqual(
                    p.layers.as_dict(),
                    {
                        "distro": {"name": "ente"},
                        "self": {
                            "description": "lib-dtproject-tests-project-basic-v4",
                            "icon": "square",
                            "maintainer": {
                                "email": "test@duckietown.com",
                                "name": "tester",
                                "organization": None,
                            },
                            "name": "lib-dtproject-tests-project-basic-v4",
                            "version": "0.0.0",
                        },
                        "template": {
                            "name": "template-basic",
                            "provider": "github.com",
                            "version": "4",
                        },
                        "base": {
                            "organization": DUCKIETOWN,
                            "registry": DEFAULT_DOCKER_REGISTRY,
                            "repository": "dt-commons",
                            "tag": None,
                        },
                        "recipes": {},
                        **layers,
                    },
                )
                # access custom layers (via dataclass)
                # noinspection PyUnresolvedReferences
                self.assertEqual(p.layers.web, layers["web"])
                # noinspection PyUnresolvedReferences
                self.assertEqual(p.layers.contributors, layers["contributors"])
                # access custom layers (via dict)
                self.assertEqual(p.layers.as_dict()["web"], layers["web"])
                self.assertEqual(p.layers.as_dict()["contributors"], layers["contributors"])

    @skip_if_code_mounted
    def test_recipe_layer_not_given(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        p = DTProject(pd)
        # make sure we know recipes were not given
        self.assertFalse(p.layers.recipes.are_given)

    @skip_if_code_mounted
    def test_recipe_layer_given_empty(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        recipes = {}
        with custom_layer(pname, "recipes", recipes):
            p = DTProject(pd)
            # make sure we know recipes are given
            self.assertTrue(p.layers.recipes.are_given)
            # compare source recipes and loaded ones
            self.assertEqual(p.layers.recipes, {})

    @skip_if_code_mounted
    def test_recipe_layer_default_only(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        recipes = {
            "default": {
                "repository": "my-recipes",
                "provider": "example.com",
                "organization": "my_username",
                "branch": "my_branch",
                "location": "./my/recipes/",
            }
        }
        with custom_layer(pname, "recipes", recipes):
            p = DTProject(pd)
            # make sure we know recipes are given
            self.assertTrue(p.layers.recipes.are_given)
            # access default
            self.assertEqual(p.layers.recipes.default, Recipe(**recipes["default"]))
            # compare source recipes and loaded ones
            self.assertEqual(
                p.layers.recipes,
                {n: Recipe(**r) for n, r in recipes.items()},
            )
