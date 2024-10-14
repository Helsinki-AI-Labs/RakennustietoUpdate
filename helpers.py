import argparse
from typing import Dict, List
from dotenv import dotenv_values
import os
import json
from typing import Dict, Any

STATE_FILE: str = "upload_state.json"


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
        # Remove file extension if present
        file = file.rsplit(".", 1)[0] if "." in file else file

        state: Dict[str, Any] = load_state()
        state.setdefault(file, {})
        state[file].update(data)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        print(f"Error updating state for {file}: {e}")
