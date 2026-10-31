import argparse
import sys
import tomllib
from pathlib import Path


def parse_design(path: Path) -> dict:
    """Flatten dependency-first sources; dependency paths are TOML-relative."""
    active: list[Path] = []
    loaded: dict[Path, dict] = {}

    def load(design_path: Path) -> dict:
        design_path = design_path.resolve()
        if design_path in active:
            chain = " -> ".join(str(item) for item in [*active, design_path])
            raise ValueError(f"Circular design dependency: {chain}")
        if design_path in loaded:
            return loaded[design_path]

        with design_path.open("rb") as f:
            config = tomllib.load(f)

        if not isinstance(config.get("top"), str):
            raise ValueError(f"Missing or invalid 'top' field in {design_path}")

        sources = config.get("sources")
        if not isinstance(sources, list) or not all(
            isinstance(source, str) for source in sources
        ):
            raise ValueError(f"Missing or invalid 'sources' array in {design_path}")

        dependencies = config.get("dependencies", [])
        if not isinstance(dependencies, list) or not all(
            isinstance(dependency, str) and dependency for dependency in dependencies
        ):
            raise ValueError(f"Invalid 'dependencies' array in {design_path}")

        active.append(design_path)
        combined_sources: list[str] = []
        for dependency in dependencies:
            dependency_config = load(design_path.parent / dependency)
            combined_sources.extend(dependency_config["sources"])
        active.pop()
        config["sources"] = list(dict.fromkeys([*combined_sources, *sources]))
        loaded[design_path] = config
        return config

    return load(path)


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
