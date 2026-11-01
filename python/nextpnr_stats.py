import argparse
import re
import sys
from pathlib import Path

RESET = "\033[0m"
BOLD = "\033[1m"

GREEN = "\033[32m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"


def parse_statistics(log: str) -> list[tuple[str, int, int, str]]:
    """Extract all resources from the final device utilization section."""
    markers = list(
        re.finditer(
            r"^Info:[ \t]*Device utili[sz]ation:[ \t]*\r?$",
            log,
            re.MULTILINE | re.IGNORECASE,
        )
    )
    if not markers:
        raise ValueError("Could not find nextpnr 'Device utilization' section")

    statistics = []
    for line in log[markers[-1].end() :].splitlines():
        if not line.strip() and not statistics:
            continue
        match = re.fullmatch(
            r"Info:\s*(?P<name>\S+):\s*(?P<used>\d+)\s*/\s*"
            r"(?P<total>\d+)\s+(?P<percent>\d+(?:\.\d+)?)%\s*",
            line,
        )
        if not match:
            if re.match(r"Info:\s*\S+:", line):
                raise ValueError(
                    f"Malformed resource utilization entry: {line.strip()}"
                )
            break
        statistics.append(
            (
                match.group("name"),
                int(match.group("used")),
                int(match.group("total")),
                match.group("percent"),
            )
        )

    if not statistics:
        raise ValueError("No resource utilization entries found in nextpnr section")
    return statistics


def format_summary(
    statistics: list[tuple[str, int, int, str]], color: bool = True
) -> str:
    """Return the device utilization summary as a string."""

    width = 46

    if color:
        reset = RESET
        bold = BOLD
        name_color = BLUE
        value_color = GREEN
        border_color = MAGENTA
    else:
        reset = ""
        bold = ""
        name_color = ""
        value_color = ""
        border_color = ""

    border_top = "+" + "-" * width + "+"
    border_middle = "+" + "-" * width + "+"
    border_bottom = "+" + "-" * width + "+"

    lines = []

    lines.append(f"{border_color}{border_top}{reset}")

    title = "Device Utilization".center(width - 2)

    lines.append(f"{border_color}|{reset} {bold}{title}{reset} {border_color}|{reset}")

    lines.append(f"{border_color}{border_middle}{reset}")

    for name, used, total, percent in statistics:
        usage = f"{used}/{total} ({percent}%)"

        lines.append(
            f"{border_color}|{reset} "
            f"{name_color}{name:<16}{reset}: "
            f"{value_color}{usage:<26}{reset} "
            f"{border_color}|{reset}"
        )

    lines.append(f"{border_color}{border_bottom}{reset}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a nextpnr log and generate a formatted device utilization report."
        )
    )

    parser.add_argument(
        "input_log",
        type=Path,
        help="nextpnr log to parse",
    )

    parser.add_argument(
        "output_log",
        type=Path,
        help="File where the formatted statistics will be written",
    )

    args = parser.parse_args()

    try:
        log = args.input_log.read_text()
    except (OSError, UnicodeError) as exc:
        print(
            f"error: could not read '{args.input_log}': {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        statistics = parse_statistics(log)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

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

    try:
        args.output_log.write_text(format_summary(statistics, color=False) + "\n")
    except OSError as exc:
        print(
            f"error: could not write '{args.output_log}': {exc}",
            file=sys.stderr,
        )
        return 1

    print(format_summary(statistics, color=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
