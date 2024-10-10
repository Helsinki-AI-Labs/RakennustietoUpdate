import argparse
from typing import Dict, List
from dotenv import dotenv_values


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
