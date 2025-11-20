import argparse
import atexit
import subprocess
import threading
import time
import os
import signal


def _start_webots(command: str, world: str) -> subprocess.Popen:
    p = subprocess.Popen(
        [command, "--batch", "--stdout", "--stderr", "--no-rendering", world],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid,
    )
    atexit.register(_kill_webots, p)
    return p


def _kill_webots(p: subprocess.Popen) -> None:
    if p.poll() is None:
        print("Killing Webots...")
        os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        p.wait(timeout=3)


def run_webots(command: str, world: str) -> None:
    def loop():
        p = _start_webots(command, world)

        while True:
            ret = p.poll()
            if ret is not None:
                print(f"Webots exited with code {ret}. Restarting...")
                _kill_webots(p)
                time.sleep(1)
                p = _start_webots(command, world)
                continue

            line = p.stdout.readline()
            if line:
                print("[WEBOTS]", line.strip())

            time.sleep(0.05)

    threading.Thread(target=loop, daemon=True).start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="webots",
        description="Script to run Webots in a subprocess",
    )
    parser.add_argument("world_file")
    parser.add_argument(
        "-e", "--executable", default="/Applications/Webots.app/Contents/MacOS/webots"
    )
    args = parser.parse_args()
    world_file = args.world_file
    webots_exec = args.executable

    try:
        run_webots(webots_exec, world_file)
    except KeyboardInterrupt:
        print("Exiting.")
