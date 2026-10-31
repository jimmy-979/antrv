"""Generate a makefile with an isolated simulation target per cocotb test."""

import argparse
import fcntl
import html
import json
import math
import os
import re
import shlex
import sys
from importlib import import_module
from pathlib import Path
from types import ModuleType
from xml.etree import ElementTree

from cocotb.regression import Test, TestGenerator


def list_tests(module: ModuleType) -> list[str]:
    names = []
    for obj in vars(module).values():
        if isinstance(obj, Test):
            names.append(obj.fullname)
        elif isinstance(obj, TestGenerator):
            names.extend(test.fullname for test in obj.generate_tests())
    return names


def get_test_result(
    result_file: Path, test_name: str, check_running: bool = True
) -> tuple[str, float | None]:
    lock_file = result_file.with_name("running.lock")
    try:
        lock = lock_file.open("r") if check_running else None
    except FileNotFoundError:
        lock = None
    if lock is not None:
        with lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return "RUNNING", None
            fcntl.flock(lock, fcntl.LOCK_UN)
    if not result_file.exists():
        return "NOT RUN", None
    root = ElementTree.parse(result_file).getroot()
    cases = [
        case
        for case in root.iter("testcase")
        if f"{case.get('classname')}.{case.get('name')}" == test_name
    ]
    if len(cases) != 1:
        raise ValueError(
            f"Expected exactly one result for {test_name} in {result_file}"
        )
    case = cases[0]
    duration_value = case.get("time")
    duration = float(duration_value) if duration_value is not None else None
    if duration is not None and (not math.isfinite(duration) or duration < 0):
        raise ValueError(f"Invalid test duration for {test_name}: {duration_value}")
    if case.find("failure") is not None or case.find("error") is not None:
        return "FAIL", duration
    elif case.find("skipped") is not None:
        return "SKIP", duration
    return "PASS", duration


def get_status(result_file: Path, test_name: str, check_running: bool = True) -> str:
    return get_test_result(result_file, test_name, check_running)[0]


def get_log_duration(log_file: Path, test_name: str) -> float | None:
    if not log_file.is_file():
        return None
    log = re.sub(r"\x1b\[[0-9;]*m", "", log_file.read_text(errors="replace"))
    number = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
    row = re.compile(
        rf"\*\*\s+{re.escape(test_name)}\s+(?:PASS|FAIL|SKIP)\s+{number}"
        rf"\s+({number})\s+{number}\s+\*\*"
    )
    durations = [float(match.group(1)) for match in row.finditer(log)]
    if not durations:
        return None
    duration = durations[-1]
    if not math.isfinite(duration) or duration < 0:
        raise ValueError(f"Invalid test duration for {test_name} in {log_file}")
    return duration


def get_log_simulation_time(log_file: Path, test_name: str) -> float | None:
    if not log_file.is_file():
        return None
    log = re.sub(r"\x1b\[[0-9;]*m", "", log_file.read_text(errors="replace"))
    number = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
    row = re.compile(
        rf"\*\*\s+{re.escape(test_name)}\s+(?:PASS|FAIL|SKIP)\s+({number})"
        rf"\s+{number}\s+{number}\s+\*\*"
    )
    durations = [float(match.group(1)) for match in row.finditer(log)]
    if not durations:
        return None
    duration = durations[-1]
    if not math.isfinite(duration) or duration < 0:
        raise ValueError(f"Invalid simulation time for {test_name} in {log_file}")
    return duration


def format_simulation_time(nanoseconds: float) -> str:
    for scale, unit in (
        (1_000_000_000, "s"),
        (1_000_000, "ms"),
        (1_000, "us"),
        (1, "ns"),
    ):
        if nanoseconds >= scale:
            return f"{nanoseconds / scale:,.3f} {unit}"
    return f"{nanoseconds:.3f} ns"


def print_status(result_file: Path, test_name: str, cached: bool = False) -> str:
    label = get_status(result_file, test_name, check_running=not cached)
    color = {"FAIL": 31, "PASS": 32, "SKIP": 33, "NOT RUN": 33, "RUNNING": 36}[label]
    suffix = " (cached; use RERUN=1 to rerun)" if cached else ""
    print(f"\033[{color}m{label}\033[0m {test_name}{suffix}")
    return label


def write_report(
    output: Path, tests: list[list[str]], build_root: Path, simulation_dir: Path
) -> None:
    rows = []
    durations = []
    simulation_times = []
    for target, name in tests:
        directory = build_root / target
        detail = ""
        simulation_time = None
        try:
            status, duration = get_test_result(directory / "results.xml", name)
            log_duration = get_log_duration(directory / "simulation.log", name)
            if log_duration is not None:
                duration = log_duration
            simulation_time = get_log_simulation_time(
                directory / "simulation.log", name
            )
        except (OSError, ElementTree.ParseError, ValueError) as exc:
            status, duration, detail = "ERROR", None, str(exc)
            print(f"Error reading {name}: {exc}", file=sys.stderr)
        duration_cell = f"{duration:.3f} s" if duration is not None else "-"
        simulation_time_cell = (
            f"{simulation_time:,.3f} ns" if simulation_time is not None else "-"
        )
        if duration is not None:
            durations.append(duration)
        if simulation_time is not None:
            simulation_times.append(simulation_time)
        log = directory / "simulation.log"
        link = (
            f'<a href="{html.escape(log.resolve().as_uri(), quote=True)}">Log</a>'
            if log.is_file()
            else ""
        )
        rows.append(
            f'<tr><td><input type="checkbox" class="test" '
            f'value="{html.escape(target, quote=True)}" '
            f'aria-label="{html.escape(target, quote=True)}"></td>'
            f"<td>{html.escape(target)}</td>"
            f'<td class="{status.lower().replace(" ", "-")}" '
            f'title="{html.escape(detail, quote=True)}">{status}</td>'
            f"<td>{duration_cell}</td>"
            f"<td>{simulation_time_cell}</td>"
            f"<td>{link}</td></tr>"
        )
    template = Path(__file__).with_name("regression_report.html").read_text()
    command = shlex.join(
        [
            "make",
            "-C",
            str(simulation_dir.resolve()),
            "-k",
            "LOG_TEST_OUTPUT=1",
            f"SIM_BUILD={build_root.resolve()}",
        ]
    )
    page = template.replace("<!-- TEST_ROWS -->", "\n".join(rows))
    total_time = f"{math.fsum(durations):.3f} s" if durations else "-"
    page = page.replace("<!-- TOTAL_TIME -->", total_time)
    total_simulation_time = (
        format_simulation_time(math.fsum(simulation_times))
        if simulation_times
        else "-"
    )
    page = page.replace("<!-- TOTAL_SIM_TIME -->", total_simulation_time)
    page = page.replace(
        "/* COMMAND_BASE */", json.dumps(command).replace("<", "\\u003c")
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page)
    print(f"\033[32mGenerated HTML report: {output.resolve()}\033[0m")


def write_makefile(test_file: Path, names: list[str], output: Path) -> None:
    def quote(value: str) -> str:
        return shlex.quote(value).replace("$", "$$")

    targets = [
        f"test-{re.sub(r'[^A-Za-z0-9_-]+', '-', name).strip('-')}" for name in names
    ]
    if len(set(targets)) != len(targets):
        raise ValueError("Test names produce duplicate Make targets after sanitization")
    lines = [
        "# Generated by list_tests.py; do not edit.",
        "ifeq ($(REGRESSION_SIM),1)",
        "ROOT = ../",
        "SIM = verilator",
        "TOPLEVEL_LANG = verilog",
        "VERILOG_SOURCES = $(shell $(PYTHON) $(PARSER) $(DESIGN) --field sources --root $(ROOT))",
        "COCOTB_TOPLEVEL = $(shell $(PYTHON) $(PARSER) $(DESIGN) --field top)",
        "include $(shell cocotb-config --makefiles)/Makefile.sim",
        "else",
        ".DEFAULT_GOAL := all",
        "LOG_TEST_OUTPUT ?= 0",
        "RERUN ?= 0",
        "all: export LOG_TEST_OUTPUT = 1",
        "",
        ".PHONY: all list-tests status html "
        + " ".join(
            targets + [f"status-{target.removeprefix('test-')}" for target in targets]
        ),
        "all: " + " ".join(targets),
        "status: "
        + " ".join(f"status-{target.removeprefix('test-')}" for target in targets),
        "",
        "list-tests:",
        "\t@printf '\\033[36m%s\\033[0m\\n' "
        + " ".join(quote(target) for target in targets),
        "",
        "HTML_REPORT ?= $(SIM_BUILD)/regression.html",
        "html:",
        f"\t@$(PYTHON) {quote(str(Path(__file__).resolve()))} "
        '--html "$(HTML_REPORT)" --build-root "$(abspath $(SIM_BUILD))" '
        f"--simulation-dir {quote(str(test_file.parent))} "
        + " ".join(
            f"--report-test {quote(target)} {quote(name)}"
            for target, name in zip(targets, names)
        ),
    ]
    simulator_dir = '"$(abspath $(SIM_BUILD))/simulator"'
    build_lock = '"$(abspath $(SIM_BUILD))/regression-build.lock"'
    for target, name in zip(targets, names):
        test_filter = quote(f"^{re.escape(name)}$")
        test_dir = f"$(abspath $(SIM_BUILD))/{target}"
        log_file = f"{test_dir}/simulation.log"
        exit_code_file = f"{test_dir}/exit_code"
        build_command = (
            f"$(MAKE) --no-print-directory -C {quote(str(test_file.parent))} "
            f"-f {quote(str(output))} REGRESSION_SIM=1 "
            f"SIM_BUILD={simulator_dir} "
            f'"$(abspath $(SIM_BUILD))/simulator/Vtop"'
        )
        command = (
            f"env COCOTB_ANSI_OUTPUT=1 COCOTB_TEST_FILTER={test_filter} "
            f"$(MAKE) --no-print-directory -C {quote(str(test_file.parent))} "
            f"-f {quote(str(output))} REGRESSION_SIM=1 "
            f"SIM_BUILD={simulator_dir} "
            f'COCOTB_RESULTS_FILE="{test_dir}/results.xml" '
            f'SIM_ARGS="$(SIM_ARGS) --trace-file {test_dir}/dump.fst" sim'
        )
        command = f"(flock -x {build_lock} {build_command} && {command})"
        lines.extend(
            [
                "",
                f"{target}:",
                f'\t@mkdir -p "{test_dir}" "$(abspath $(SIM_BUILD))/simulator"',
                f'\t+@exec 9>"{test_dir}/running.lock"; \\',
                "\tflock -n 9 || { printf '\\033[36m%s\\033[0m\\n' "
                f"{quote('RUNNING ' + name + ' (already running)')} >&2; exit 1; }}; \\",
                f'\tif [ "$(RERUN)" != 1 ] && [ -f "{test_dir}/results.xml" ]; then \\',
                (
                    f"\t\t$(PYTHON) {quote(str(Path(__file__).resolve()))} "
                    f'--status "{test_dir}/results.xml" --test-name {quote(name)} --cached; \\'
                ),
                "\t\texit $$?; \\",
                "\tfi; \\",
                f'\trm -f "{test_dir}/results.xml"; \\',
                f'\trm -f "{exit_code_file}"; \\',
                '\tif [ "$(LOG_TEST_OUTPUT)" = 1 ]; then '
                f"printf '\\033[36mRUN\\033[0m %s\\n' {quote(name)}; fi; \\",
                f'\t{{ {command}; result=$$?; printf "%s\\n" "$$result" > "{exit_code_file}"; }} '
                f'2>&1 | tee "{log_file}"; \\',
                "\ttee_result=$$?; \\",
                f'\tif [ ! -f "{exit_code_file}" ]; then \\',
                (
                    "\t\tprintf '\\033[31m%s\\033[0m\\n' "
                    f"{quote('FAIL ' + name + ' (simulation exited before reporting status)')}; \\"
                ),
                "\t\texit 1; \\",
                "\tfi; \\",
                f'\tresult=$$(cat "{exit_code_file}"); rm -f "{exit_code_file}"; \\',
                "\tif [ $$tee_result -ne 0 ]; then \\",
                (
                    "\t\tprintf '\\033[31m%s\\033[0m\\n' "
                    f"{quote('FAIL ' + name + ' (could not write simulation log)')}; \\"
                ),
                "\t\texit 1; \\",
                "\tfi; \\",
                "\tif [ $$result -eq 0 ]; then \\",
                '\t\tif [ "$(LOG_TEST_OUTPUT)" = 1 ]; then \\',
                f"\t\t\tprintf '\\033[32mPASS\\033[0m %s\\n' {quote(name)}; \\",
                "\t\tfi; \\",
                "\telse \\",
                (
                    "\t\tprintf '\\033[31mFAIL\\033[0m %s (log: %s)\\n' "
                    f'{quote(name)} "{log_file}"; \\'
                ),
                "\t\texit $$result; \\",
                "\tfi",
                "",
                f"status-{target.removeprefix('test-')}:",
                (
                    f"\t@$(PYTHON) {quote(str(Path(__file__).resolve()))} "
                    f'--status "{test_dir}/results.xml" --test-name {quote(name)}'
                ),
            ]
        )
    lines.append("endif")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "test_file", nargs="?", type=Path, help="Path to a cocotb test file"
    )
    parser.add_argument(
        "--status", type=Path, help="Print status from a test result XML"
    )
    parser.add_argument("--test-name", help="Fully qualified test name for --status")
    parser.add_argument("--html", type=Path, help="Write an HTML regression report")
    parser.add_argument("--build-root", type=Path, default=Path("build"))
    parser.add_argument("--simulation-dir", type=Path, default=Path.cwd())
    parser.add_argument("--report-test", nargs=2, action="append", default=[])
    parser.add_argument(
        "--cached",
        action="store_true",
        help="Mark status as cached and return failure for a saved failing test",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("build/regression.mk"),
        help="Generated makefile path (default: build/regression.mk)",
    )
    args = parser.parse_args()
    if args.html is not None:
        write_report(args.html, args.report_test, args.build_root, args.simulation_dir)
        return
    if args.status is not None:
        if args.test_name is None:
            parser.error("--status requires --test-name")
        try:
            label = print_status(args.status, args.test_name, cached=args.cached)
        except (OSError, ElementTree.ParseError, ValueError) as exc:
            parser.exit(1, f"Error reading test status: {exc}\n")
        if args.cached and label not in ("PASS", "SKIP"):
            parser.exit(1)
        return
    if args.test_file is None:
        parser.error("test_file is required when not using --status")
    test_file = args.test_file.resolve()
    output = args.output.resolve()
    if not test_file.is_file() or test_file.suffix != ".py":
        parser.error(f"Expected an existing Python test file: {test_file}")

    # Match simulation imports and relative paths, including ELF discovery.
    sys.path.insert(0, str(test_file.parent))
    os.chdir(test_file.parent)
    module = import_module(test_file.stem)
    names = list_tests(module)
    if not names:
        parser.exit(1, f"No cocotb tests found in {test_file}\n")
    write_makefile(test_file, names, output)
    print(f"\033[32mGenerated {output} with {len(names)} test targets\033[0m")


if __name__ == "__main__":
    main()
