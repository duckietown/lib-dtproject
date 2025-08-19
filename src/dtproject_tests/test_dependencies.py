import unittest

from dtproject import DTProject

from . import get_project_path


class TestDependencies(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_dependencies_project_v1(self):
        pd = get_project_path("basic_v1")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.apt_dependencies(), [])
        self.assertEqual(p.py3_dependencies(), ["dep1"])

    def test_dependencies_project_v2(self):
        pd = get_project_path("basic_v2")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.apt_dependencies(), ["dep2"])
        self.assertEqual(p.py3_dependencies(), ["dep2", "dep2a"])

    def test_dependencies_project_v3(self):
        pd = get_project_path("basic_v3")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.apt_dependencies(), ["dep3", "dep3a"])
        self.assertEqual(p.py3_dependencies_dt(), ["dep3a"])
        self.assertEqual(p.py3_dependencies(), ["dep3b", "dep3c"])

    def test_dependencies_project_v4(self):
        pd = get_project_path("basic_v4")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.apt_dependencies(), ["dep4"])
        self.assertEqual(p.py3_dependencies_dt(), ["dep4a", "dep4b"])
        self.assertEqual(p.py3_dependencies(), ["dep4c", "dep4d"])
