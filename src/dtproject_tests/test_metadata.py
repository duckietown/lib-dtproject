import unittest

from dtproject import DTProject

from . import get_project_path


class TestMetadata(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_metadata_project_v1(self):
        pd = get_project_path("basic_v1")
        p = DTProject(pd)
        # ---
        self.assertEqual(
            p.metadata,
            {
                "VERSION": "0.0.0",
                "TYPE": "template-basic",
                "TYPE_VERSION": "1",
                "PATH": pd,
            },
        )

    def test_metadata_project_v2(self):
        pd = get_project_path("basic_v2")
        p = DTProject(pd)
        # ---
        self.assertEqual(
            p.metadata,
            {
                "VERSION": "0.0.0",
                "TYPE": "template-basic",
                "TYPE_VERSION": "2",
                "PATH": pd,
            },
        )

    def test_metadata_project_v3(self):
        pd = get_project_path("basic_v3")
        p = DTProject(pd)
        # ---
        self.assertEqual(
            p.metadata,
            {
                "VERSION": "0.0.0",
                "TYPE": "template-basic",
                "TYPE_VERSION": "3",
                "PATH": pd,
            },
        )

    def test_metadata_project_v4(self):
        pd = get_project_path("basic_v4")
        p = DTProject(pd)
        # ---
        self.assertEqual(
            p.metadata,
            {
                "VERSION": "0.0.0",
                "TYPE": "template-basic",
                "TYPE_VERSION": "4",
                "PATH": pd,
            },
        )
