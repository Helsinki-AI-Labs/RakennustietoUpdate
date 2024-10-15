import argparse
from typing import Dict, List
from dotenv import dotenv_values
import os
import json
from typing import Dict, Any

STATE_FILE: str = "state.json"


def parse_args(
    required_args: List[str], optional_args: List[str] = []
) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    for arg in required_args:
        parser.add_argument(arg, required=True, help=f"CLI argument {arg} is required")
    for arg in optional_args:
        parser.add_argument(arg, required=False, help=f"CLI argument {arg} is optional")
    return parser.parse_args()


def check_args_and_env_vars(
    required_args: List[str] = [],
    required_env_vars: List[str] = [],
    optional_args: List[str] = [],
) -> Dict[str, str | None]:
    config: Dict[str, str | None] = dotenv_values(".env")
    args = parse_args(required_args, optional_args)
    for arg in required_args:
        # Given arg --from_dir will set config.FROM_DIR to args.from_dir
        config.setdefault(arg[2:].upper(), args.__getattribute__(arg[2:]))
    for arg in optional_args:
        if args.__getattribute__(arg[2:]):
            config.setdefault(arg[2:].upper(), args.__getattribute__(arg[2:]))
    for env_var in required_env_vars:
        if env_var not in config:
            raise ValueError(f"Missing required environment variable: {env_var}")

    return config


def load_state() -> Dict[str, Any]:
    """Load the upload state from a JSON file."""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(
            f"Warning: {STATE_FILE} is not a valid JSON. Starting with an empty state."
        )
        return {}


def update_state(file: str, data: Dict[str, Any]) -> None:
    """Update the state with the provided data for a given key."""
    try:
        filename = os.path.basename(file)
        filename = filename.rsplit(".", 1)[0] if "." in filename else filename

        state: Dict[str, Any] = load_state()
        state.setdefault(filename, {})
        state[filename].update(data)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        print(f"Error updating state for {filename}: {e}")


def get_section_id(file_path: str, section_index: int) -> str:
    """
    Generates a section ID by removing the path and extension from the filename
    and appending the section index.

    Args:
        file_path (str): The path to the file or the filename.
        section_index (int): The index of the section.

    Returns:
        str: The section ID in the format 'filename-index'.
    """
    filename = os.path.basename(file_path)
    name, _ = os.path.splitext(filename)
    return f"{name}-{section_index}"


def combine_title_content(section: dict) -> str:
    """
    Combines the title and content of a section into a single string.

    Args:
        section (dict): The section dictionary containing title and content.

    Returns:
        str: The combined title and content.
    """
    title = section.get("title", "").strip()
    content = section.get("content", [])
    combined_content = f"{title}\n\n\n" + "\n".join(content)
    return combined_content
