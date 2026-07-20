import os
import pty
import select
import subprocess
import sys
import threading
import time


DEMO_STEPS = (
    ("10k + 25", 0.8),
    (":format si", 0.8),
    ("10000", 0.8),
    (":angles dms", 0.8),
    ("90deg / 2", 0.8),
    ("values = [1, 2, 3, 4, 5]", 1.0),
    (":head values 3", 0.8),
    ("mean(values)", 0.8),
    ("linreg([1, 2, 3], [2, 4, 6])", 1.0),
    (":show ans", 1.0),
    ("quit", 0.3),
)


def _relay_output(master_fd):
    while True:
        ready, _, _ = select.select([master_fd], [], [], 0.1)
        if master_fd not in ready:
            continue

        try:
            chunk = os.read(master_fd, 4096)
        except OSError:
            break

        if not chunk:
            break

        os.write(sys.stdout.fileno(), chunk)


def _type_line(master_fd, text):
    for character in text:
        os.write(master_fd, character.encode("utf-8"))
        time.sleep(0.035)
    os.write(master_fd, b"\n")


def main():
    master_fd, slave_fd = pty.openpty()
    environment = dict(os.environ)
    environment.setdefault("TERM", "xterm-256color")

    process = subprocess.Popen(
        ["python3", "-m", "slowcrunch"],
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        env=environment,
        close_fds=True,
    )
    os.close(slave_fd)

    relay_thread = threading.Thread(target=_relay_output, args=(master_fd,), daemon=True)
    relay_thread.start()

    time.sleep(1.2)
    for line, pause_after in DEMO_STEPS:
        _type_line(master_fd, line)
        time.sleep(pause_after)

    process.wait()
    relay_thread.join(timeout=1.0)
    os.close(master_fd)
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
