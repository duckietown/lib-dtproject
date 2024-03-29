from dtproject.types import Hook, LayerHooks
from . import get_project_path

from dtproject import DTProject
import unittest


class TestLayerSelf(unittest.TestCase):

    def test_layer_self_project_v1(self):
        pd = get_project_path("basic_v1")
        p = DTProject(pd)
        # ---

    def test_layer_self_project_v2(self):
        pd = get_project_path("basic_v2")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.name, "basic_v2")
        self.assertEqual(p.version, "0.0.0")

    def test_layer_self_project_v3(self):
        pd = get_project_path("basic_v3")
        p = DTProject(pd)
        # ---

    def test_layer_self_project_v4(self):
        pd = get_project_path("basic_v4")
        p = DTProject(pd)
        # ---
        self.assertEqual(p.hooks, LayerHooks(hooks={}))
        self.assertEqual(p.hooks.hooks["non-existent-hook"], [])
        self.assertEqual(p.hooks.hooks.get("non-existent-hook"), [])
        self.assertEqual(p.hooks.hooks.get("non-existent-hook", []), [])


    def test_layer_self_project_v4_custom(self):
        pd = get_project_path("custom_v4")
        p = DTProject(pd)
        # ---
        self.assertEqual(
            p.hooks,
            LayerHooks(hooks={
                'pre-build': [Hook(command='echo "pre-build hook"', required=True)],
                'post-build': [Hook(command='echo "post-build hook"', required=True)]
            })
        )

        # Test for LayerHooks.__iter__
        for e, h in p.hooks:
            if e == 'pre-build':
                self.assertEqual(h, [Hook(command='echo "pre-build hook"', required=True)])
            elif e == 'post-build':
                self.assertEqual(h, [Hook(command='echo "post-build hook"', required=True)])

        # Test for LayerHooks.__getitem__
        self.assertEqual(p.hooks['pre-build'], [Hook(command='echo "pre-build hook"', required=True)])
        self.assertEqual(p.hooks['non-existent-hook'], [])
       
        # Test for LayerHooks.get
        self.assertEqual(p.hooks.get('pre-build'), [Hook(command='echo "pre-build hook"', required=True)])
        self.assertEqual(p.hooks.get('non-existent-hook'), [])

        

if __name__ == '__main__':
    TestLayerSelf().test_layer_self_project_v4_custom()