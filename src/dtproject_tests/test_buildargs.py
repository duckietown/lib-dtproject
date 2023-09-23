import unittest

from dtproject import DTProject

from . import get_project_path


class TestBuildArgs(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_buildargs_project_v1(self):
        pd = get_project_path("basic_v1")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.build_args, {})

    def test_buildargs_project_v2(self):
        pd = get_project_path("basic_v2")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.build_args, {})

    def test_buildargs_project_v3(self):
        pd = get_project_path("basic_v3")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.build_args, {})

    def test_buildargs_project_v4(self):
        pd = get_project_path("basic_v4")
        p = DTProject(pd)
        # ---
        self.assertEqual(
            p.build_args,
            {
                "BASE_ORGANIZATION": "duckietown",
                "BASE_REPOSITORY": "dt-commons",
                "DISTRO": "ente",
                "PROJECT_DESCRIPTION": "lib-dtproject-tests-project-basic-v4",
                "PROJECT_FORMAT_VERSION": 4,
                "PROJECT_ICON": "square",
                "PROJECT_MAINTAINER": "tester (test@duckietown.com)",
                "PROJECT_NAME": "lib-dtproject-tests-project-basic-v4",
            },
        )

    def test_buildargs_project_v4_custom(self):
        pd = get_project_path("custom_v4")
        p = DTProject(pd)
        # ---
        self.assertEqual(
            p.build_args,
            {
                "BASE_ORGANIZATION": "myorganization",
                "BASE_REPOSITORY": "myrepository",
                "DISTRO": "ente",
                "PROJECT_DESCRIPTION": "lib-dtproject-tests-project-basic-v4",
                "PROJECT_FORMAT_VERSION": 4,
                "PROJECT_ICON": "square",
                "PROJECT_MAINTAINER": "tester (test@duckietown.com)",
                "PROJECT_NAME": "lib-dtproject-tests-project-basic-v4",
                # extras
                "BASE_TAG": "mytag",
            },
        )
