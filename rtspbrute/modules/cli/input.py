import argparse
from pathlib import Path
from typing import Any

from rtspbrute import DEFAULT_CREDENTIALS, DEFAULT_ROUTES, __version__


class CustomHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=40, width=99)

    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ", ".join(action.option_strings) + " " + args_string


def file_path(value: Any):
    if Path(value).exists():
        return Path(value)
    else:
        raise argparse.ArgumentTypeError(f"{value} is not a valid path")


def port(value: Any):
    if int(value) in range(65536):
        return int(value)
    else:
        raise argparse.ArgumentTypeError(f"{value} is not a valid port")


fmt = lambda prog: CustomHelpFormatter(prog)
parser = argparse.ArgumentParser(
    prog="rtspbrute",
    description="Tool for RTSP that brute-forces routes and credentials, makes screenshots!",
    formatter_class=fmt,
)
parser.add_argument(
    "-t",
    "--targets",
    type=file_path,
    required=True,
    help="the targets on which to scan for open RTSP streams",
)
parser.add_argument(
    "-p",
    "--ports",
    nargs="+",
    default=[554],
    type=port,
    help="the ports on which to search for RTSP streams",
)
parser.add_argument(
    "-r",
    "--routes",
    type=file_path,
    default=DEFAULT_ROUTES,
    help="the path on which to load a custom routes",
)
parser.add_argument(
    "-c",
    "--credentials",
    type=file_path,
    default=DEFAULT_CREDENTIALS,
    help="the path on which to load a custom credentials",
)
parser.add_argument(
    "-ct",
    "--check-threads",
    default=500,
    type=int,
    help="the number of threads to brute-force the routes",
    metavar="N",
)
parser.add_argument(
    "-bt",
    "--brute-threads",
    default=200,
    type=int,
    help="the number of threads to brute-force the credentials",
    metavar="N",
)
parser.add_argument(
    "-st",
    "--screenshot-threads",
    default=20,
    type=int,
    help="the number of threads to screenshot the streams",
    metavar="N",
)
parser.add_argument(
    "-T", "--timeout", default=2, type=int, help="the timeout to use for sockets"
)
parser.add_argument("-d", "--debug", action="store_true", help="enable the debug logs")
parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
