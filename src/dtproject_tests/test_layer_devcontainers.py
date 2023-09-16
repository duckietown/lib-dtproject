import unittest

from dtproject import DTProject
from dtproject.types import DevContainerConfiguration

from . import (
    get_project_path,
    skip_if_code_mounted,
    devcontainers_layer,
)


class TestLayerDevContainers(unittest.TestCase):

    def test_layer_devcontainers_project_v1(self):
        pd = get_project_path("basic_v1")
        p = DTProject(pd)
        # we expect no devcontainers
        self.assertEqual(p.devcontainers, {})

    def test_layer_devcontainers_project_v2(self):
        pd = get_project_path("basic_v2")
        p = DTProject(pd)
        # we expect no devcontainers
        self.assertEqual(p.devcontainers, {})

    def test_layer_devcontainers_project_v3(self):
        pd = get_project_path("basic_v3")
        p = DTProject(pd)
        # we expect no devcontainers
        self.assertEqual(p.devcontainers, {})

    def test_layer_devcontainers_project_v4(self):
        pd = get_project_path("basic_v4")
        p = DTProject(pd)
        # we expect no devcontainers
        self.assertEqual(p.devcontainers, {})

    @skip_if_code_mounted
    def test_layer_devcontainers_not_given(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        p = DTProject(pd)
        # make sure we know devcontainers were not given
        self.assertFalse(p.layers.devcontainers.are_given)

    @skip_if_code_mounted
    def test_layer_devcontainers_given_empty(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        devcontainers = {}
        with devcontainers_layer(pname, devcontainers):
            p = DTProject(pd)
            # make sure we know devcontainers are given
            self.assertTrue(p.layers.devcontainers.are_given)
            # compare source devcontainers and loaded ones
            self.assertEqual(p.layers.devcontainers, {})

    @skip_if_code_mounted
    def test_layer_devcontainers_just_one(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        devcontainers = {
            "my-container": {
                "image": "my-image",
                "network": "host",
                "privileged": True
            }
        }
        with devcontainers_layer(pname, devcontainers):
            p = DTProject(pd)
            # make sure the devcontainers are preserved
            self.assertEqual(p.layers.devcontainers, DevContainerConfiguration(**devcontainers))
            self.assertEqual(
                p.layers.devcontainers,
                {n: DevContainerConfiguration(**r) for n, r in devcontainers.items()},
            )

    @skip_if_code_mounted
    def test_layer_devcontainers_more_devcontainers(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        devcontainers = {
            "container1": {
                "image": "my-image-1",
                "network": "host",
                "privileged": True
            },
            "container2": {
                "image": "my-image-2",
                "network": "bridge",
                "privileged": False
            },
        }
        with devcontainers_layer(pname, devcontainers):
            p = DTProject(pd)
            # compare source devcontainers and loaded ones
            self.assertEqual(p.layers.devcontainers, DevContainerConfiguration(**devcontainers))
            self.assertEqual(
                p.layers.devcontainers,
                {n: DevContainerConfiguration(**r) for n, r in devcontainers.items()},
            )
