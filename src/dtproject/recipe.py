import json
import os
import time

import requests
from dtproject.types import Recipe

from . import logger
from .exceptions import RecipeProjectNotFound, DTProjectError
from .utils.misc import run_cmd

RECIPE_STAGE_NAME = "recipe"
MEAT_STAGE_NAME = "meat"
CHECK_RECIPE_UPDATE_MINS = 5

DUCKIETOWN_HOME = os.environ.get("DUCKIETOWN_HOME", os.path.expanduser("~/.duckietown"))


def get_recipes_dir() -> str:
    default_recipes_dir: str = os.path.join(DUCKIETOWN_HOME, "recipes")
    return os.environ.get("DUCKIETOWN_RECIPES", default_recipes_dir)


def get_recipe_repo_dir(recipe: Recipe) -> str:
    repository, branch = recipe.repository, recipe.branch
    return os.path.join(get_recipes_dir(), repository, branch)


def get_recipe_project_dir(recipe: Recipe) -> str:
    repository, location = recipe.repository, recipe.location
    return os.path.join(get_recipe_repo_dir(recipe), location.strip("/"))


def recipe_project_exists(recipe: Recipe) -> bool:
    recipe_dir: str = get_recipe_project_dir(recipe)
    return os.path.exists(recipe_dir) and os.path.isdir(recipe_dir)


def clone_recipe(recipe: Recipe) -> bool:
    """
    Args:
        recipe: the recipe to clone
    """
    repository, organization, branch, provider = recipe.repository, recipe.organization, recipe.branch, recipe.provider
    recipe_dir: str = get_recipe_project_dir(recipe)
    if recipe_project_exists(recipe):
        raise DTProjectError(f"Recipe already exists at '{recipe_dir}'")

    # Clone recipes repo into dt-shell root
    try:
        repo_dir: str = get_recipe_repo_dir(recipe)
        logger.info(f"Downloading recipes...")
        logger.debug(f"Downloading recipes into '{repo_dir}' ...")
        remote_url: str = f"https://{provider}/{organization}/{repository}"
        run_cmd(["git", "clone", "-b", branch, "--recurse-submodules", remote_url, repo_dir])
        logger.info(f"Recipes downloaded!")
        return True
    except Exception as e:
        # Excepts as InvalidRemote
        logger.error(f"Unable to clone the repo '{repository}'. {str(e)}.")
        return False


def recipe_needs_update(recipe: Recipe) -> bool:
    repository, branch = recipe.repository, recipe.branch
    recipe_dir: str = get_recipe_project_dir(recipe)
    need_update = False
    # Get the current repo info
    commands_update_check_flag = os.path.join(recipe_dir, ".updates-check")

    # Check if it's time to check for an update
    if os.path.exists(commands_update_check_flag) and os.path.isfile(commands_update_check_flag):
        now = time.time()
        last_time_checked = os.path.getmtime(commands_update_check_flag)
        use_cached_recipe = now - last_time_checked < CHECK_RECIPE_UPDATE_MINS * 60
    else:  # Save the initial .update flag
        local_sha: str = run_cmd(["git", "-C", recipe_dir, "rev-parse", "HEAD"])[0]
        # noinspection PyTypeChecker
        local_sha = next(filter(len, local_sha.split("\n")))
        save_update_check_flag(recipe_dir, local_sha)
        return False

    # Check for an updated remote
    if not use_cached_recipe:
        # Get the local sha from file (ok if oos from manual pull)
        with open(commands_update_check_flag, "r") as fp:
            try:
                cached_check = json.load(fp)
            except ValueError:
                return False
            local_sha = cached_check["remote"]

        # Get the remote sha from GitHub
        logger.info("Fetching remote SHA from github.com ...")
        # TODO: this should be conditioned on the provider, we have github hard-coded instead
        remote_url: str = f"https://api.github.com/repos/{repository}/branches/{branch}"
        try:
            data: dict = requests.get(remote_url).json()
            remote_sha = data["commit"]["sha"]
        except Exception as e:
            logger.error(str(e))
            return False

        # check if we need to update
        need_update = local_sha != remote_sha
        # touch flag to reset update check time
        touch_update_check_flag(recipe_dir)

    return need_update


def save_update_check_flag(recipe_dir: str, sha: str) -> None:
    commands_update_check_flag = os.path.join(recipe_dir, ".updates-check")
    with open(commands_update_check_flag, "w") as fp:
        json.dump({"remote": sha}, fp)


def touch_update_check_flag(recipe_dir: str) -> None:
    commands_update_check_flag = os.path.join(recipe_dir, ".updates-check")
    with open(commands_update_check_flag, "a"):
        os.utime(commands_update_check_flag, None)


def update_recipe(recipe: Recipe) -> bool:
    branch: str = recipe.branch
    recipe_dir: str = get_recipe_project_dir(recipe)
    if not recipe_project_exists(recipe):
        raise RecipeProjectNotFound(f"There is no existing recipe in '{recipe_dir}'.")

    # Check for recipe repo updates
    logger.info("Checking if the project's recipe needs to be updated...")
    if recipe_needs_update(recipe):
        logger.info("This project's recipe has available updates. Attempting to pull them.")
        logger.debug(f"Updating recipe '{recipe_dir}'...")
        wait_on_retry_secs = 4
        th = {2: "nd", 3: "rd", 4: "th"}
        for trial in range(3):
            try:
                run_cmd(["git", "-C", recipe_dir, "pull", "--recurse-submodules", "origin", branch])
                logger.debug(f"Updated recipe in '{recipe_dir}'.")
                logger.info(f"Recipe successfully updated!")
            except RuntimeError as e:
                logger.error(str(e))
                logger.warning(
                    "An error occurred while pulling the updated commands. Retrying for "
                    f"the {trial + 2}-{th[trial + 2]} in {wait_on_retry_secs} seconds."
                )
                time.sleep(wait_on_retry_secs)
            else:
                break
        run_cmd(["git", "-C", recipe_dir, "submodule", "update"])

        # Get HEAD sha after update and save
        current_sha: str = run_cmd(["git", "-C", recipe_dir, "rev-parse", "HEAD"])
        # noinspection PyTypeChecker
        current_sha = next(filter(len, current_sha.split("\n")))
        save_update_check_flag(recipe_dir, current_sha)
        return True  # Done updating
    else:
        logger.info(f"Recipe is up-to-date.")
        return False
