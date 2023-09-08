from . import get_project_path

from dtproject import DTProject
import unittest


class TestMetaDistro(unittest.TestCase):

    def test_meta_project_v1(self):
        pd = get_project_path("basic_v1")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.distro, "latest")

    def test_meta_project_v2(self):
        pd = get_project_path("basic_v2")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.distro, "latest")

    def test_meta_project_v3(self):
        pd = get_project_path("basic_v3")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.distro, "latest")

    def test_meta_project_v4(self):
        pd = get_project_path("basic_v4")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.distro, "ente")
