import argparse
import re
import sys
from pathlib import Path

# ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"

CYAN = "\033[36m"
GREEN = "\033[32m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"


def parse_statistics(log):
    """Extract local statistics from the final Yosys statistics section."""

    marker_pos = log.rfind("Printing statistics.")

    if marker_pos == -1:
        raise ValueError("Could not find Yosys 'Printing statistics.' section")

    stats_log = log[marker_pos:]

    # Find the module name.
    module_match = re.search(
        r"^===\s+(?P<module>.+?)\s+===\s*$",
        stats_log,
        re.MULTILINE,
    )

    if not module_match:
        raise ValueError("Could not find module name in statistics section")

    module = module_match.group("module").strip()

    hierarchy_match = re.search(
        r"^===\s+design hierarchy\s+===\s*$",
        stats_log,
        re.MULTILINE,
    )

    if hierarchy_match:
        local_stats = stats_log[module_match.end() : hierarchy_match.start()]
    else:
        # No design hierarchy section. Since we only care about
        # local statistics, use everything after the module header.
        local_stats = stats_log[module_match.end() :]

    statistics = []

    for line in local_stats.splitlines():
        # Ignore formatting lines.
        if not line.strip():
            continue

        if line.strip().startswith("+"):
            continue

        if line.strip() == "|":
            continue

        # Yosys aligns the count column independently from the
        # hierarchy. The hierarchy is represented by the whitespace
        # between the count and the name.
        #
        # Example:
        #
        #       4 cells
        #       4   SB_RAM40_4K
        #
        # The first has one space between "4" and "cells".
        # The second has three spaces between "4" and "SB_RAM40_4K".
        match = re.match(
            r"^\s*(?P<count>\d+)(?P<separator>\s+)(?P<name>\S.*)$",
            line,
        )

        if not match:
            continue

        count = int(match.group("count"))
        name = match.group("name").strip()

        separator = match.group("separator")

        # One space means a top-level statistic.
        # Additional spaces indicate a child entry.
        #
        # Yosys currently uses three spaces for child entries,
        # but we preserve the actual distinction rather than
        # depending on specific names.
        indent = max(0, len(separator) - 1)

        statistics.append((indent, name, count))

    return {
        "module": module,
        "statistics": statistics,
    }


def format_summary(stats, color=True):
    """Return the synthesis summary as a string."""

    module = stats["module"]
    statistics = stats["statistics"]

    width = 46

    if color:
        reset = RESET
        bold = BOLD
        module_color = CYAN
        name_color = BLUE
        value_color = GREEN
        border_color = MAGENTA
    else:
        reset = ""
        bold = ""
        module_color = ""
        name_color = ""
        value_color = ""
        border_color = ""

    border_top = "╭" + "─" * width + "╮"
    border_middle = "├" + "─" * width + "┤"
    border_bottom = "╰" + "─" * width + "╯"

    lines = []

    lines.append(f"{border_color}{border_top}{reset}")

    title = "Synthesis Summary".center(width - 2)

    lines.append(f"{border_color}│{reset} {bold}{title}{reset} {border_color}│{reset}")

    lines.append(f"{border_color}{border_middle}{reset}")

    lines.append(
        f"{border_color}│{reset} "
        f"{bold}{module_color}{'Module':<16}{reset}: "
        f"{value_color}{module:<26}{reset} "
        f"{border_color}│{reset}"
    )

    lines.append(f"{border_color}│{reset} {' ' * (width - 2)} {border_color}│{reset}")

    for indent, name, count in statistics:
        display_name = (" " * indent) + name

        lines.append(
            f"{border_color}│{reset} "
            f"{name_color}{display_name:<16}{reset}: "
            f"{value_color}{count:<26}{reset} "
            f"{border_color}│{reset}"
        )

    lines.append(f"{border_color}{border_bottom}{reset}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Parse a Yosys synthesis log and generate "
            "a formatted synthesis statistics report."
        )
    )

    parser.add_argument(
        "input_log",
        type=Path,
        help="Yosys synthesis log to parse",
    )

    parser.add_argument(
        "output_log",
        type=Path,
        help="File where the formatted statistics will be written",
    )

    args = parser.parse_args()

    # --------------------------------------------------------------
    # Read input log
    # --------------------------------------------------------------

    try:
        log = args.input_log.read_text()
    except OSError as exc:
        print(
            f"error: could not read '{args.input_log}': {exc}",
            file=sys.stderr,
        )
        return 1

    # --------------------------------------------------------------
    # Parse statistics
    # --------------------------------------------------------------

    try:
        stats = parse_statistics(log)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # --------------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------------

    try:
        args.output_log.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
    except OSError as exc:
        print(
            f"error: could not create output directory "
            f"'{args.output_log.parent}': {exc}",
            file=sys.stderr,
        )
        return 1

    # --------------------------------------------------------------
    # Write plain-text report
    # --------------------------------------------------------------

    try:
        args.output_log.write_text(format_summary(stats, color=False) + "\n")
    except OSError as exc:
        print(
            f"error: could not write '{args.output_log}': {exc}",
            file=sys.stderr,
        )
        return 1

    # --------------------------------------------------------------
    # Print colored report to terminal
    # --------------------------------------------------------------

    print(format_summary(stats, color=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
