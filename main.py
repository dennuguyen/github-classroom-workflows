import argparse
import tempfile

from discover_tests import discover_tests
from run_tests import run_tests
from webots import run_webots

parser = argparse.ArgumentParser(
    prog="main",
    description="Python script to autotest Webots",
)
parser.add_argument("test_file")
parser.add_argument("test_executable")
parser.add_argument(
    "--webots", default="/Applications/Webots.app/Contents/MacOS/webots"
)
args = parser.parse_args()

config_file = tempfile.NamedTemporaryFile()

world_file = "worlds/arena.wbt"

run_webots(args.webots, world_file)
discover_tests(args.test_file, config_file.name)
result = run_tests(args.test_executable, config_file.name)
print(result)
