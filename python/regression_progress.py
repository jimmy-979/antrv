"""Display regression progress while preserving Make output and exit status."""

import argparse
import os
import re
import selectors
import shutil
import signal
import subprocess
import sys
import time


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run(command: list[str], total: int) -> int:
    started = time.monotonic()
    running: set[str] = set()
    finished: dict[str, str] = {}
    cached: set[str] = set()
    interactive = sys.stdout.isatty()

    def summary(compact: bool = False) -> str:
        seconds = int(time.monotonic() - started)
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        completed = len(finished)
        filled = min(10, completed * 10 // total) if total else 10
        bar = "#" * filled + "-" * (10 - filled)
        if compact:
            return (
                f"[{bar}] {completed}/{total} | "
                f"{hours:02}:{minutes:02}:{seconds:02} | "
                f"Passed: {list(finished.values()).count('PASS')} | "
                f"Failed: {list(finished.values()).count('FAIL')} | "
                f"Running: {len(running)}"
            )
        return (
            f"[{bar}] Tests: {completed}/{total} completed | Running: {len(running)} | "
            f"Passed: {list(finished.values()).count('PASS')} | "
            f"Failed: {list(finished.values()).count('FAIL')} | "
            f"Cached: {len(cached)} | Elapsed: {hours:02}:{minutes:02}:{seconds:02}"
        )

    def styled(text: str) -> str:
        if not interactive:
            return text
        text = re.sub(r"\[[#-]+\]", lambda match: f"\033[36m{match[0]}\033[0m", text)
        for label, color in (("Passed", 32), ("Failed", 31), ("Running", 36), ("Cached", 33)):
            text = re.sub(
                rf"{label}: \d+",
                lambda match: f"\033[{color}m{match[0]}\033[0m",
                text,
            )
        return text

    def draw() -> None:
        if interactive:
            width = max(1, shutil.get_terminal_size().columns - 1)
            text = summary()
            if len(text) > width:
                text = summary(compact=True)
            print("\r\033[2K" + styled(text[:width]), end="", flush=True)

    def output(line: str) -> None:
        plain = ANSI.sub("", line)
        match = re.match(r"^(RUN|PASS|FAIL|SKIP) (\S+)(.*)$", plain)
        if match:
            status, name, suffix = match.groups()
            if status == "RUN":
                running.add(name)
            else:
                running.discard(name)
                finished[name] = status
                if "(cached;" in suffix:
                    cached.add(name)
        if interactive:
            print("\r\033[2K", end="")
        print(line, flush=True)
        draw()

    # Recursive Make's jobserver descriptors must reach the child Make process.
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        close_fds=False, start_new_session=True,
    )
    assert process.stdout is not None
    pending = b""
    interrupted = False
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        draw()
        try:
            while selector.get_map():
                for key, _ in selector.select(timeout=1):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        break
                    pending += chunk
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        output(line.decode(errors="replace"))
                draw()
            if pending:
                output(pending.decode(errors="replace"))
            result = process.wait()
        except KeyboardInterrupt:
            interrupted = True
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            result = 130
        finally:
            process.stdout.close()
            if interactive:
                print("\r\033[2K", end="")
            print(styled(summary()) + (" | Interrupted" if interrupted else ""), flush=True)
    return result if result >= 0 else 128 - result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--make", default="make")
    parser.add_argument("--makefile", required=True)
    args = parser.parse_args()
    command = [args.make, "--no-print-directory", "-f", args.makefile]
    discovery = subprocess.run(
        command + ["-s", "list-tests"], capture_output=True, text=True,
        close_fds=False,
    )
    if discovery.returncode:
        sys.stderr.write(discovery.stdout + discovery.stderr)
        raise SystemExit(discovery.returncode)
    names = [
        ANSI.sub("", line) for line in discovery.stdout.splitlines()
        if ANSI.sub("", line).startswith("test-")
    ]
    raise SystemExit(run(command + ["all"], len(names)))


if __name__ == "__main__":
    main()
