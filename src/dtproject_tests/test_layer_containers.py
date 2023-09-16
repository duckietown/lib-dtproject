import unittest

from dtproject import DTProject
from dtproject.types import ContainerConfiguration

from . import (
    get_project_path,
    skip_if_code_mounted,
    containers_layer,
)


class TestLayerContainers(unittest.TestCase):

    def test_layer_containers_project_v1(self):
        pd = get_project_path("basic_v1")
        p = DTProject(pd)
        # we expect no containers
        self.assertEqual(p.containers, {})

    def test_layer_containers_project_v2(self):
        pd = get_project_path("basic_v2")
        p = DTProject(pd)
        # we expect no containers
        self.assertEqual(p.containers, {})

    def test_layer_containers_project_v3(self):
        pd = get_project_path("basic_v3")
        p = DTProject(pd)
        # we expect no containers
        self.assertEqual(p.containers, {})

    def test_layer_containers_project_v4(self):
        pd = get_project_path("basic_v4")
        p = DTProject(pd)
        # we expect no containers
        self.assertEqual(p.containers, {})

    @skip_if_code_mounted
    def test_layer_container_not_given(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        p = DTProject(pd)
        # make sure we know containers were not given
        self.assertFalse(p.layers.containers.are_given)

    @skip_if_code_mounted
    def test_layer_container_given_empty(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        containers = {}
        with containers_layer(pname, containers):
            p = DTProject(pd)
            # make sure we know containers are given
            self.assertTrue(p.layers.containers.are_given)
            # compare source containers and loaded ones
            self.assertEqual(p.layers.containers, {})

    @skip_if_code_mounted
    def test_layer_container_just_one(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        containers = {
            "my-container": {
                "image": "my-image",
                "network": "host",
                "privileged": True
            }
        }
        with containers_layer(pname, containers):
            p = DTProject(pd)
            # make sure the containers are preserved
            self.assertEqual(p.layers.containers, ContainerConfiguration(**containers))
            self.assertEqual(
                p.layers.containers,
                {n: ContainerConfiguration(**r) for n, r in containers.items()},
            )

    @skip_if_code_mounted
    def test_layer_container_more_containers(self):
        pname = "basic_v4"
        pd = get_project_path(pname)
        containers = {
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
        with containers_layer(pname, containers):
            p = DTProject(pd)
            # compare source containers and loaded ones
            self.assertEqual(p.layers.containers, ContainerConfiguration(**containers))
            self.assertEqual(
                p.layers.containers,
                {n: ContainerConfiguration(**r) for n, r in containers.items()},
            )
