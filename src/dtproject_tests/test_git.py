from . import get_project_path, git_repository, skip_if_code_mounted

from dtproject import DTProject
import unittest


class TestGitProject(unittest.TestCase):

    @skip_if_code_mounted
    def test_git_project_v1to3_empty(self):
        pname = "basic_v1"
        pdir = get_project_path(pname)
        # just an empty repository
        with git_repository(pname):
            p = DTProject(pdir)
            # ---
            self.assertEqual(p.name, pname)
            self.assertEqual(p.distro, "master")

    @skip_if_code_mounted
    def test_git_project_v1to3_just_remote(self):
        pname = "basic_v1"
        pdir = get_project_path(pname)
        # just the remote
        repo_name: str = "basic_git_v1"
        with git_repository(pname, remote=f"git@github.com:does_not_matter/{repo_name}"):
            p = DTProject(pdir)
            # ---
            self.assertEqual(p.name, repo_name)
            self.assertEqual(p.distro, "master")

    @skip_if_code_mounted
    def test_git_project_v1to3_just_branch(self):
        pname = "basic_v1"
        pdir = get_project_path(pname)
        # just the branch
        branch_name: str = "ente-new-feature"
        with git_repository(pname, branch=branch_name):
            p = DTProject(pdir)
            # ---
            self.assertEqual(p.name, pname)
            self.assertEqual(p.distro, "ente")
            self.assertEqual(p.version_name, branch_name)

    @skip_if_code_mounted
    def test_layer_git_project_v4_just_branch(self):
        pname = "basic_v4"
        pdir = get_project_path(pname)
        # just the branch
        branch_name: str = "ente-new-feature"
        with git_repository(pname, branch=branch_name):
            p = DTProject(pdir)
            # ---
            self.assertEqual(p.distro, "ente")
            self.assertEqual(p.version_name, branch_name)

    @skip_if_code_mounted
    def test_layer_git_project_v4_just_remote(self):
        pname = "basic_v4"
        pdir = get_project_path(pname)
        # just the branch
        repo_name: str = "basic_git_v4"
        with git_repository(pname, remote=f"git@github.com:does_not_matter/{repo_name}"):
            p = DTProject(pdir)
            # ---
            # v4+ does not use the remote to get a name for the project
            self.assertNotEqual(p.name, repo_name)
