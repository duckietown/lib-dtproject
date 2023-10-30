from . import get_project_path

from dtproject import DTProject
import unittest

# template-autolab                          v2
# template-basic                            v3
# template-book                             v2
# template-compose                          v3
# template-core                             v2
# template-library                          v1
# template-lx                               v3
# template-lx-recipe                        v3
# template-machine-learning                 v2
# template-machine-learning-pytorch         v2
# template-ros                              v3


class TestLayerTemplate(unittest.TestCase):

    def test_daffy_template_autolab(self):
        pd = get_project_path("daffy/template-autolab")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.type, "template-ros")
        self.assertEqual(p.type_version, "2")

    def test_daffy_template_basic(self):
        pd = get_project_path("daffy/template-basic")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.type, "template-basic")
        self.assertEqual(p.type_version, "3")

    def test_daffy_template_book(self):
        pd = get_project_path("daffy/template-book")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.type, "template-book")
        self.assertEqual(p.type_version, "2")

    def test_daffy_template_compose(self):
        pd = get_project_path("daffy/template-compose")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.type, "template-compose")
        self.assertEqual(p.type_version, "3")

    def test_daffy_template_core(self):
        pd = get_project_path("daffy/template-core")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.type, "template-core")
        self.assertEqual(p.type_version, "2")

    def test_daffy_template_library(self):
        pd = get_project_path("daffy/template-library")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.type, "template-library")
        self.assertEqual(p.type_version, "1")

    def test_daffy_template_lx(self):
        pd = get_project_path("daffy/template-lx")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.type, "template-exercise")
        self.assertEqual(p.type_version, "3")

    def test_daffy_template_lx_recipe(self):
        pd = get_project_path("daffy/template-lx-recipe")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.type, "template-exercise-recipe")
        self.assertEqual(p.type_version, "3")

    def test_daffy_template_machine_learning(self):
        pd = get_project_path("daffy/template-machine-learning")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.type, "template-basic")
        self.assertEqual(p.type_version, "2")

    def test_daffy_template_machine_learning_pytorch(self):
        pd = get_project_path("daffy/template-machine-learning-pytorch")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.type, "template-basic")
        self.assertEqual(p.type_version, "2")

    def test_daffy_template_ros_commons(self):
        pd = get_project_path("daffy/template-ros")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.type, "template-ros")
        self.assertEqual(p.type_version, "3")
