from . import get_project_path

from dtproject import DTProject
import unittest


class TestMetaSelf(unittest.TestCase):

    def test_meta_project_v1(self):
        pd = get_project_path("basic_v1")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.name, "basic_v1")
        self.assertEqual(p.version, "0.0.0")

    def test_meta_project_v2(self):
        pd = get_project_path("basic_v2")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.name, "basic_v2")
        self.assertEqual(p.version, "0.0.0")

    def test_meta_project_v3(self):
        pd = get_project_path("basic_v3")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.name, "basic_v3")
        self.assertEqual(p.version, "0.0.0")

    def test_meta_project_v4(self):
        pd = get_project_path("basic_v4")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.name, "lib-dtproject-tests-project-basic-v4")
        self.assertEqual(p.version, "0.0.0")
        # new to v4
        self.assertEqual(p.description, "lib-dtproject-tests-project-basic-v4")
        self.assertEqual(p.maintainer, "tester (test@duckietown.com)")
        self.assertEqual(p.icon, "square")
