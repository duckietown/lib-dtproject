import unittest

from dtproject import DTProject
from dtproject.exceptions import InconsistentDTProject
from dtproject.types import Recipe

from . import get_project_path, skip_if_code_mounted, value, recipes_layer, options_layer


class TestLayerRecipes(unittest.TestCase):

    def test_layer_recipes_project_v1(self):
        pd = get_project_path("basic_v1")
        p = DTProject(pd)
        # we expect no recipes
        self.assertEqual(p.recipes, {})

    def test_layer_recipes_project_v2(self):
        pd = get_project_path("basic_v2")
        p = DTProject(pd)
        # we expect no recipes
        self.assertEqual(p.recipes, {})

    def test_layer_recipes_project_v3(self):
        pd = get_project_path("basic_v3")
        p = DTProject(pd)
        # we expect no recipes
        self.assertEqual(p.recipes, {})

    def test_layer_recipes_project_v4(self):
        pd = get_project_path("basic_v4")
        p = DTProject(pd)
        # we expect no recipes
        self.assertEqual(p.recipes, {})

    @skip_if_code_mounted
    def test_layer_recipe_not_given(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        p = DTProject(pd)
        # make sure we know recipes were not given
        self.assertFalse(p.layers.recipes.are_given)

    @skip_if_code_mounted
    def test_layer_recipe_given_empty(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        recipes = {}
        with recipes_layer(pname, recipes):
            p = DTProject(pd)
            # make sure we know recipes are given
            self.assertTrue(p.layers.recipes.are_given)
            # compare source recipes and loaded ones
            self.assertEqual(p.layers.recipes, {})

    @skip_if_code_mounted
    def test_layer_recipe_missing_option(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        recipes = {
            "default": {
                "repository": "my-recipes",
                "branch": "my_branch",
            }
        }
        with recipes_layer(pname, recipes):
            with self.assertRaises(InconsistentDTProject):
                _ = DTProject(pd)

    @skip_if_code_mounted
    def test_layer_recipe_default_only(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        recipes = {
            "default": {
                "repository": "my-recipes",
                "branch": "my_branch",
            }
        }
        with options_layer(pname, {"needs_recipe": True}):
            with recipes_layer(pname, recipes):
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

    @skip_if_code_mounted
    def test_layer_recipe_no_default(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        recipes = {
            "my-recipe": {
                "repository": "my-recipes",
                "branch": "my_branch",
            }
        }
        with options_layer(pname, {"needs_recipe": True}):
            with recipes_layer(pname, recipes):
                # if we don't select the recipe when 'default' is not defined, we get a ValueError
                with self.assertRaises(ValueError):
                    _ = DTProject(pd)
                # choose the recipe explicitly
                p = DTProject(pd, recipe="my-recipe")
                # access default
                self.assertEqual(p.layers.recipes.default, None)

    @skip_if_code_mounted
    def test_layer_recipe_selected_wrong(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        recipes = {
            "my-recipe": {
                "repository": "my-recipes",
                "branch": "my_branch",
            }
        }
        with options_layer(pname, {"needs_recipe": True}):
            with recipes_layer(pname, recipes):
                # if we don't select the recipe when 'default' is not defined, we get a ValueError
                with self.assertRaises(ValueError):
                    _ = DTProject(pd, recipe="wrong-recipe")

    @skip_if_code_mounted
    def test_layer_recipe_selected_when_not_needed(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        with options_layer(pname, {"needs_recipe": False}):
            # if we attempt to select a recipe when the project does not need recipes, we get a ValueError
            with self.assertRaises(ValueError):
                _ = DTProject(pd, recipe="unneded-recipe")

    @skip_if_code_mounted
    def test_layer_recipe_properties(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        recipes = {
            "my-recipe": {
                "repository": "my-recipes",
                "provider": "example.com",
                "organization": "my_username",
                "branch": "my_branch",
                "location": "./my/recipes/",
            }
        }
        with options_layer(pname, {"needs_recipe": True}):
            with recipes_layer(pname, recipes):
                # choose the recipe explicitly
                p = DTProject(pd, recipe="my-recipe")
                # make sure the properties are preserved
                self.assertEqual(p.layers.recipes["my-recipe"], Recipe(**recipes["my-recipe"]))

    @skip_if_code_mounted
    def test_layer_recipe_more_recipes(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        recipes = {
            "recipe1": {
                "repository": "my-recipes",
                "provider": "example.com",
                "organization": "my_username",
                "branch": "my_branch",
                "location": "./my/recipes/recipe1/",
            },
            "recipe2": {
                "repository": "my-recipes",
                "provider": "example.com",
                "organization": "my_username",
                "branch": "my_branch",
                "location": "./my/recipes/recipe2/",
            }
        }
        with options_layer(pname, {"needs_recipe": True}):
            with recipes_layer(pname, recipes):
                p = DTProject(pd, recipe="recipe1")
                # compare source recipes and loaded ones
                self.assertEqual(
                    p.layers.recipes,
                    {n: Recipe(**r) for n, r in recipes.items()},
                )

    @skip_if_code_mounted
    def test_layer_recipe_custom_selected_recipe(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        recipes = {
            "recipe1": {
                "repository": "my-recipes",
                "provider": "example.com",
                "organization": "my_username",
                "branch": "my_branch",
                "location": "./my/recipes/recipe1/",
            },
            "recipe2": {
                "repository": "my-recipes",
                "provider": "example.com",
                "organization": "my_username",
                "branch": "my_branch",
                "location": "./my/recipes/recipe2/",
            }
        }
        with options_layer(pname, {"needs_recipe": True}):
            with recipes_layer(pname, recipes):
                # check selected recipe 1/2
                with value("recipe1") as recipe:
                    p = DTProject(pd, recipe=recipe)
                    self.assertEqual(p.recipe_info, Recipe(**recipes[recipe]))
                # check selected recipe 2/2
                with value("recipe2") as recipe:
                    p = DTProject(pd, recipe=recipe)
                    self.assertEqual(p.recipe_info, Recipe(**recipes[recipe]))
