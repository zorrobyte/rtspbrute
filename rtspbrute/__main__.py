import collections
import logging
import platform
import threading
import time
from pathlib import Path
from queue import Queue
from typing import Callable, List

import av
from rich.panel import Panel

from rtspbrute.modules import attack, utils, worker
from rtspbrute.modules.cli.input import parser
from rtspbrute.modules.cli.output import console, progress_bar
from rtspbrute.modules.rtsp import RTSPClient


def start_threads(number: int, target: Callable, *args) -> List[threading.Thread]:
    threads = []
    for _ in range(number):
        thread = threading.Thread(target=target, args=args)
        thread.daemon = True
        threads.append(thread)
        thread.start()
    return threads


def wait_for(queue: Queue, threads: List[threading.Thread]):
    """Waits for queue and then threads to finish."""
    queue.join()
    [queue.put(None) for _ in range(len(threads))]
    [t.join() for t in threads]


def main():
    args = parser.parse_args()

    # Folders and files set up
    start_datetime = time.strftime("%Y.%m.%d-%H.%M.%S")
    REPORT_FOLDER = Path.cwd() / "reports" / start_datetime
    attack.PICS_FOLDER = REPORT_FOLDER / "pics"
    utils.RESULT_FILE = REPORT_FOLDER / "result.txt"
    utils.HTML_FILE = REPORT_FOLDER / "index.html"
    utils.create_folder(attack.PICS_FOLDER)
    utils.create_file(utils.RESULT_FILE)
    utils.generate_html(utils.HTML_FILE)

    # Logging module set up
    logger = logging.getLogger()
    attack.logger_is_enabled = args.debug
    if args.debug:
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(REPORT_FOLDER / "debug.log")
        file_handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(threadName)s] [%(funcName)s] %(message)s"
            )
        )
        logger.addHandler(file_handler)
    # This disables ValueError from av module printing to console, but this also
    # means we won't get any logs from av, if they aren't FATAL or PANIC level.
    av.logging.set_level(av.logging.FATAL)

    # Progress output set up
    worker.PROGRESS_BAR = progress_bar
    worker.CHECK_PROGRESS = progress_bar.add_task("[bright_red]Checking...", total=0)
    worker.BRUTE_PROGRESS = progress_bar.add_task("[bright_yellow]Bruting...", total=0)
    worker.SCREENSHOT_PROGRESS = progress_bar.add_task(
        "[bright_green]Screenshoting...", total=0
    )

    # Targets, routes, credentials and ports set up
    targets = collections.deque(set(utils.load_txt(args.targets, "targets")))
    attack.ROUTES = utils.load_txt(args.routes, "routes")
    attack.CREDENTIALS = utils.load_txt(args.credentials, "credentials")
    attack.PORTS = args.ports

    check_queue = Queue()
    brute_queue = Queue()
    screenshot_queue = Queue()

    if platform.system() == "Linux":
        import resource

        _, _max = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (_max, _max))
        console.print(f"[yellow]Temporary ulimit -n set to {_max}")

    if args.debug:
        logger.debug(f"Starting {args.check_threads} threads of worker.brute_routes")
    check_threads = start_threads(
        args.check_threads, worker.brute_routes, check_queue, brute_queue
    )
    if args.debug:
        logger.debug(
            f"Starting {args.brute_threads} threads of worker.brute_credentials"
        )
    brute_threads = start_threads(
        args.brute_threads, worker.brute_credentials, brute_queue, screenshot_queue
    )
    if args.debug:
        logger.debug(
            f"Starting {args.screenshot_threads} threads of worker.screenshot_targets"
        )
    screenshot_threads = start_threads(
        args.screenshot_threads, worker.screenshot_targets, screenshot_queue
    )

    console.print("[green]Starting...\n")

    progress_bar.update(worker.CHECK_PROGRESS, total=len(targets))
    progress_bar.start()
    while targets:
        check_queue.put(RTSPClient(ip=targets.popleft(), timeout=args.timeout))

    wait_for(check_queue, check_threads)
    if args.debug:
        logger.debug("Check queue and threads finished")
    wait_for(brute_queue, brute_threads)
    if args.debug:
        logger.debug("Brute queue and threads finished")
    wait_for(screenshot_queue, screenshot_threads)
    if args.debug:
        logger.debug("Screenshot queue and threads finished")

    progress_bar.stop()

    print()
    screenshots = list(attack.PICS_FOLDER.iterdir())
    console.print(f"[green]Saved {len(screenshots)} screenshots")
    console.print(
        Panel(f"[bright_green]{str(REPORT_FOLDER)}", title="Report", expand=False),
        justify="center",
    )


if __name__ == "__main__":
    main()
