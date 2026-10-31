import argparse
import sys
import tomllib
from pathlib import Path


def parse_design(path: Path) -> dict:
    with path.open("rb") as f:
        config = tomllib.load(f)

    if not isinstance(config.get("top"), str):
        raise TypeError("Missing or invalid 'top' field")

    sources = config.get("sources")
    if not isinstance(sources, list) or not all(
        isinstance(source, str) for source in sources
    ):
        raise ValueError("Missing or invalid 'sources' array")

    return config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument(
        "--field",
        choices=["top", "sources"],
        required=True,
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Root directory to prefix source paths (default: .)",
    )
    args = parser.parse_args()

    try:
        config = parse_design(args.config)
    except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.field == "top":
        print(config["top"])
    else:
        for source in config["sources"]:
            print(args.root / source)


if __name__ == "__main__":
    main()
